from flask import Flask, render_template, request, jsonify, Response
import os
import sys
import json
from threading import Thread
import time
import re
from datetime import datetime

# Add parent directory to path so we can import agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.agent import Agent
from computers.default.local_playwright import LocalPlaywrightBrowser

app = Flask(__name__, template_folder='templates', static_folder='static')

# Store active tasks and their status
tasks = {}

# Track current test session ID
current_session_id = None

# Test case report file path
REPORT_FILE = os.path.join(os.path.dirname(__file__), 'test_reports', 'test_case_report.json')

def ensure_report_directory():
    """Ensure the test_reports directory exists."""
    report_dir = os.path.dirname(REPORT_FILE)
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

def extract_url_from_instructions(instructions):
    """Extract URL from instructions if present."""
    urls = re.findall(r'(?P<url>https?://[^\s]+)', instructions)
    return urls[0] if urls else None

def extract_testcase_info(instructions):
    """Extract test case number and description from instructions."""
    # Pattern: TestCase Number - 1001.1.1.1, Description
    pattern = r'TestCase Number\s*-\s*([0-9.]+)\s*,\s*([^:]+):'
    match = re.search(pattern, instructions, re.IGNORECASE)
    
    if match:
        test_case_number = match.group(1).strip()
        test_case_name = match.group(2).strip()
        return test_case_number, test_case_name
    return None, None

def extract_all_testcases(instructions):
    """Extract all test case numbers and descriptions from instructions."""
    pattern = r'TestCase Number\s*-\s*([0-9.]+)\s*,\s*([^:]+):'
    matches = re.finditer(pattern, instructions, re.IGNORECASE)
    
    test_cases = []
    for match in matches:
        test_case_number = match.group(1).strip()
        test_case_name = match.group(2).strip()
        test_cases.append({
            'number': test_case_number,
            'name': test_case_name,
            'start_pos': match.start()
        })
    
    return test_cases

def split_instructions_by_testcase(instructions):
    """Split instructions into separate test case blocks."""
    test_cases = extract_all_testcases(instructions)
    
    if not test_cases:
        return [(None, None, instructions)]
    
    result = []
    for i, tc in enumerate(test_cases):
        start = tc['start_pos']
        # Find the start of this test case block (go backwards to find beginning)
        block_start = 0
        if i > 0:
            # Start after the previous test case
            prev_end = test_cases[i-1]['start_pos']
            # Find where previous test case validation ends
            validation_pattern = r'Update the result in one word \(Pass/Fail\) in report against this test case number\.'
            prev_section = instructions[:start]
            validation_matches = list(re.finditer(validation_pattern, prev_section, re.IGNORECASE))
            if validation_matches:
                block_start = validation_matches[-1].end()
        
        # Find the end of this test case block
        if i < len(test_cases) - 1:
            block_end = test_cases[i + 1]['start_pos']
            # Find the validation statement end
            section = instructions[start:block_end]
            validation_match = re.search(r'Update the result in one word \(Pass/Fail\) in report against this test case number\.', section, re.IGNORECASE)
            if validation_match:
                block_end = start + validation_match.end()
        else:
            block_end = len(instructions)
        
        block_text = instructions[block_start:block_end].strip()
        result.append((tc['number'], tc['name'], block_text))
    
    return result

def parse_pass_fail_from_output(output_text):
    """Parse Pass/Fail result from agent output."""
    output_lower = output_text.lower()
    
    # Get the last 500 characters for final verdict analysis
    last_part = output_text[-500:].lower() if len(output_text) > 500 else output_lower
    
    # Look for explicit Pass/Fail at the end (highest priority)
    if last_part.strip().endswith('pass') or last_part.strip().endswith('passed'):
        return 'Pass'
    if last_part.strip().endswith('fail') or last_part.strip().endswith('failed'):
        return 'Fail'
    
    # Check for explicit statements
    if 'test case is passed' in last_part or 'result: pass' in last_part:
        return 'Pass'
    if 'test case is failed' in last_part or 'result: fail' in last_part:
        return 'Fail'
    
    # Failure indicators (check first as they're more critical)
    fail_indicators = [
        'unable to', 'cannot', 'error', 'failed', 'failure', 
        'incorrect', 'does not match', 'not found', 'not visible',
        'blocked', 'denied', 'locked out'
    ]
    
    for indicator in fail_indicators:
        if indicator in output_lower:
            return 'Fail'
    
    # Success indicators
    success_indicators = [
        'passed', 'successful', 'verified', 'correct', 'appears correctly',
        'displayed', 'loaded', 'visible', 'confirmation', 'completed successfully'
    ]
    
    for indicator in success_indicators:
        if indicator in output_lower:
            return 'Pass'
    
    return 'Unknown'

def save_test_case_result(test_case_number, test_case_name, result, screenshot_b64, terminal_output, instructions, session_id):
    """Save test case result to JSON report file."""
    ensure_report_directory()
    
    # Check if we need to start a new session (clear old results)
    report = None
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            existing_report = json.load(f)
            # If session_id matches, keep the report; otherwise start fresh
            if existing_report.get("session_id") == session_id:
                report = existing_report
    
    # Create new report if needed
    if report is None:
        report = {
            "test_suite": "Sauce Demo Automation Test Suite",
            "session_id": session_id,
            "execution_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_cases": []
        }
    
    # Create test case entry
    test_case_entry = {
        "test_case_number": test_case_number,
        "test_case_name": test_case_name,
        "result": result,
        "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "instructions": instructions.strip(),
        "terminal_output": terminal_output,
        "screenshot": screenshot_b64 if screenshot_b64 else None  # Store full screenshot for export
    }
    
    # Append to report
    report["test_cases"].append(test_case_entry)
    
    # Update summary statistics
    total = len(report["test_cases"])
    passed = sum(1 for tc in report["test_cases"] if tc["result"] == "Pass")
    failed = sum(1 for tc in report["test_cases"] if tc["result"] == "Fail")
    unknown = sum(1 for tc in report["test_cases"] if tc["result"] == "Unknown")
    
    report["summary"] = {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "unknown": unknown,
        "pass_rate": f"{(passed/total*100):.2f}%" if total > 0 else "0%"
    }
    
    # Save report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Test Case {test_case_number} - {result} - Saved to report")
    return report

def run_cua_task(task_id, instructions):
    global current_session_id
    computer = None
    
    try:
        # Create a new session ID for this test run
        session_id = f"session_{int(time.time() * 1000)}"
        current_session_id = session_id
        
        print(f"\n{'='*70}")
        print(f"Starting New Test Session: {session_id}")
        print(f"Previous test results will be cleared")
        print(f"{'='*70}\n")
        
        # Split instructions into separate test cases
        test_case_blocks = split_instructions_by_testcase(instructions)
        
        if len(test_case_blocks) > 1:
            print(f"\n{'='*70}")
            print(f"Detected {len(test_case_blocks)} test cases to execute")
            print(f"{'='*70}\n")
        
        # Initialize the computer and agent once for all test cases
        computer = LocalPlaywrightBrowser(headless=False)
        computer.__enter__()  # This ensures the browser is properly initialized
        
        # Extract URL from instructions if present and navigate to it
        start_url = extract_url_from_instructions(instructions)
        if start_url:
            computer.goto(start_url)
            
        agent = Agent(computer=computer)
        
        # Process each test case
        for test_case_number, test_case_name, test_case_instructions in test_case_blocks:
            if test_case_number:
                print(f"\n{'='*70}")
                print(f"Starting Test Case: {test_case_number} - {test_case_name}")
                print(f"{'='*70}\n")
            
            # Run single test case
            run_single_testcase(
                task_id=task_id,
                test_case_number=test_case_number,
                test_case_name=test_case_name,
                instructions=test_case_instructions,
                computer=computer,
                agent=agent,
                session_id=session_id
            )
            
            # Brief pause between test cases
            if test_case_number and len(test_case_blocks) > 1:
                time.sleep(2)
        
        # Mark overall task as completed
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = f"All test cases completed. Total: {len(test_case_blocks)}"
        
    except Exception as e:
        # Update task status with error
        error_msg = str(e)
        print(f"Error occurred: {error_msg}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["message"] = f"Error: {error_msg}"
    finally:
        # Make sure we clean up the computer/browser
        if computer:
            try:
                computer.__exit__(None, None, None)
            except:
                pass

def run_single_testcase(task_id, test_case_number, test_case_name, instructions, computer, agent, session_id):
    """Run a single test case and save results."""
    # Update task status
    tasks[task_id]["status"] = "running"
    tasks[task_id]["message"] = f"Running test case {test_case_number}" if test_case_number else "Task started"
    tasks[task_id]["needs_input"] = False
    tasks[task_id]["prompt"] = None
    tasks[task_id]["test_case_number"] = test_case_number
    tasks[task_id]["test_case_name"] = test_case_name
    
    try:
        # Check if we need to navigate to a URL for this test
        start_url = extract_url_from_instructions(instructions)
        if start_url:
            print(f"Navigating to: {start_url}")
            computer.goto(start_url)
            computer.wait(2000)  # Wait for page load
        
        # Convert instructions into properly formatted input items with roles
        # Add context about being in browser automation mode
        enhanced_instructions = f"""You are controlling a real browser for automated testing.
Execute the following test case step by step.
After completing all verification steps, provide a clear final verdict.
State either "Pass" or "Fail" as your final answer.

{instructions}"""
        
        input_items = [
            {
                "role": "user",
                "content": enhanced_instructions
            }
        ]
        
        # Run the agent with interactive prompt handling
        max_turns = 20  # Prevent infinite loops
        turn_count = 0
        
        while turn_count < max_turns:
            # Update task with current step
            if "needs_input" in tasks[task_id] and tasks[task_id]["needs_input"]:
                # Wait for user response
                while tasks[task_id]["needs_input"]:
                    time.sleep(0.5)
                
                # Get user response and add to input items
                user_response = tasks[task_id].get("user_response", "")
                input_items.append({
                    "role": "user",
                    "content": user_response
                })
            
            # Run the agent with verbose logging
            turn_count += 1
            print(f"\nExecuting agent turn {turn_count}/{max_turns}...")
            output_items = agent.run_full_turn(input_items, print_steps=True)
            print(f"Agent turn {turn_count} completed")
            
            # Process output items to separate terminal output from agent messages
            terminal_output = []
            last_output = ""
            
            if output_items:
                print(f"DEBUG: Processing {len(output_items)} output items")
                for item in output_items:
                    if isinstance(item, dict):
                        print(f"DEBUG: Item type: {item.get('type')}")
                        
                        # Extract screenshot from computer_call_output
                        if item.get("type") == "computer_call_output":
                            output_data = item.get("output", {})
                            print(f"DEBUG: Output data type: {output_data.get('type')}")
                            if output_data.get("type") == "input_image":
                                image_url = output_data.get("image_url", "")
                                # Extract base64 data from data:image/png;base64,<data>
                                if image_url.startswith("data:image/png;base64,"):
                                    screenshot_b64 = image_url.split(",", 1)[1]
                                    tasks[task_id]["screenshot"] = screenshot_b64
                                    print(f"DEBUG: Screenshot captured, length: {len(screenshot_b64)}")
                        
                        # Capture ALL message content (including reasoning and regular messages)
                        content = item.get("content", "")
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict):
                                    if "text" in c:
                                        text = c["text"].strip()
                                        if text:  # Only add non-empty text
                                            terminal_output.append(text)
                                            last_output = text
                        elif isinstance(content, str) and content.strip():
                            terminal_output.append(content.strip())
                            last_output = content.strip()
                    else:
                        last_output = str(item)
                        terminal_output.append(last_output)
            
            # Update task with terminal output
            tasks[task_id]["terminal_output"] = "\n".join(terminal_output)
            
            print(f"Last output: {last_output}")
            
            # Convert to lowercase for checking
            last_output_lower = last_output.lower()
            
            # Check if this is a test case completion (looking for Pass/Fail indication)
            is_test_case_complete = False
            terminal_output_str = "\n".join(terminal_output)
            
            # Check if the agent explicitly states pass/fail at the END of output
            if test_case_number:
                # Look for pass/fail in last output or if "tell us" question was answered
                if (last_output.strip().lower() in ['pass', 'fail', 'passed', 'failed'] or
                    "test case is passed" in last_output_lower or
                    "test case is failed" in last_output_lower or
                    "result: pass" in last_output_lower or
                    "result: fail" in last_output_lower):
                    is_test_case_complete = True
            
            # Check for various types of prompts that need user input
            # But auto-respond to procedural questions during test execution
            needs_input = False
            auto_response = None
            
            if "?" in last_output:
                # Auto-respond to procedural questions
                if ("should i" in last_output_lower or "proceed" in last_output_lower or
                    "shall i" in last_output_lower or "go ahead" in last_output_lower):
                    auto_response = "yes, proceed"
                    print(f"Auto-responding to procedural question: '{last_output}' with 'yes, proceed'")
                elif "do you want" in last_output_lower or "would you like" in last_output_lower:
                    auto_response = "yes"
                    print(f"Auto-responding to question: '{last_output}' with 'yes'")
                else:
                    # For non-procedural questions, mark as needing input
                    needs_input = True
            
            # If test case is complete, save the result
            if is_test_case_complete and test_case_number:
                result = parse_pass_fail_from_output(terminal_output_str)
                screenshot_b64 = tasks[task_id].get("screenshot", "")
                
                # Save test case result to JSON report
                save_test_case_result(
                    test_case_number=test_case_number,
                    test_case_name=test_case_name,
                    result=result,
                    screenshot_b64=screenshot_b64,
                    terminal_output=terminal_output_str,
                    instructions=instructions,
                    session_id=session_id
                )
                
                print(f"\n{'='*70}")
                print(f"Test Case {test_case_number} - Result: {result}")
                print(f"{'='*70}\n")
                
                # Mark this test case as completed (but don't break - return instead)
                tasks[task_id]["message"] = f"Test Case {test_case_number} completed - {result}"
                tasks[task_id]["test_result"] = result
                return  # Exit this test case, continue to next one
            
            # Handle auto-response to procedural questions
            if auto_response:
                input_items.append({
                    "role": "user",
                    "content": auto_response
                })
                # Continue the loop to process the auto-response
                continue
            
            if needs_input:
                print(f"Agent needs input: {last_output}")
                tasks[task_id]["needs_input"] = True
                tasks[task_id]["prompt"] = last_output
                tasks[task_id]["status"] = "waiting_for_input"
                tasks[task_id]["message"] = "Waiting for user input"
            else:
                # Check for various completion signals
                print(f"Processing agent output: {last_output}")
                
                if not needs_input and "completed" in last_output_lower:
                    # Only ask for next steps if the task appears to be completed
                    print("Task completed, prompting for next steps")
                    tasks[task_id]["needs_input"] = True
                    tasks[task_id]["prompt"] = "Task completed. Would you like me to do anything else?"
                    tasks[task_id]["status"] = "completed"
                    tasks[task_id]["message"] = "Task completed"
                else:
                    # Continue with the current instruction flow
                    print("Continuing with current instructions")
                    tasks[task_id]["needs_input"] = False
                    tasks[task_id]["status"] = "running"
        
        # If we reach here, max turns exceeded without explicit pass/fail
        if test_case_number and turn_count >= max_turns:
            print(f"Warning: Max turns ({max_turns}) reached without clear pass/fail verdict")
            terminal_output_str = "\n".join(terminal_output)
            result = parse_pass_fail_from_output(terminal_output_str)
            
            if result == 'Unknown':
                result = 'Fail'  # Default to Fail if unclear after max turns
                terminal_output_str += "\n\n[Test incomplete: Maximum execution turns reached]"
            
            screenshot_b64 = tasks[task_id].get("screenshot", "")
            
            save_test_case_result(
                test_case_number=test_case_number,
                test_case_name=test_case_name,
                result=result,
                screenshot_b64=screenshot_b64,
                terminal_output=terminal_output_str,
                instructions=instructions,
                session_id=session_id
            )
            
            print(f"\n{'='*70}")
            print(f"Test Case {test_case_number} - Result: {result} (Max turns reached)")
            print(f"{'='*70}\n")
        
    except Exception as e:
        # Update task status with error
        error_msg = str(e)
        print(f"Error occurred in test case {test_case_number}: {error_msg}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["message"] = f"Error: {error_msg}"
        
        # If this was a test case, save it as failed
        if test_case_number:
            save_test_case_result(
                test_case_number=test_case_number,
                test_case_name=test_case_name or "Unknown Test",
                result="Fail",
                screenshot_b64=tasks[task_id].get("screenshot", ""),
                terminal_output=f"Error: {error_msg}",
                instructions=instructions,
                session_id=session_id
            )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/send-task', methods=['POST'])
def send_task():
    data = request.get_json() or {}
    instructions = data.get('instructions', '')
    
    if not instructions:
        return jsonify({
            'status': 'error',
            'message': 'No instructions provided'
        }), 400
    
    # Create a new task
    task_id = str(int(time.time() * 1000))
    tasks[task_id] = {
        "status": "pending",
        "message": "Task queued",
        "instructions": instructions
    }
    
    # Start task in background
    thread = Thread(target=run_cua_task, args=(task_id, instructions))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'ok',
        'message': 'Task started',
        'task_id': task_id
    })

@app.route('/api/task-status/<task_id>')
def task_status(task_id):
    if task_id not in tasks:
        return jsonify({
            'status': 'error',
            'message': 'Task not found'
        }), 404
    
    return jsonify(tasks[task_id])

@app.route('/api/respond-to-prompt/<task_id>', methods=['POST'])
def respond_to_prompt(task_id):
    if task_id not in tasks:
        return jsonify({
            'status': 'error',
            'message': 'Task not found'
        }), 404
    
    data = request.get_json() or {}
    response = data.get('response', '')
    
    if not response:
        return jsonify({
            'status': 'error',
            'message': 'No response provided'
        }), 400
    
    tasks[task_id]["user_response"] = response
    tasks[task_id]["needs_input"] = False
    
    return jsonify({
        'status': 'ok',
        'message': 'Response received'
    })

@app.route('/api/test-report', methods=['GET'])
def get_test_report():
    """Retrieve the complete test case report."""
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            report = json.load(f)
        return jsonify(report)
    else:
        return jsonify({
            'status': 'error',
            'message': 'No test report available yet'
        }), 404

@app.route('/api/test-report/clear', methods=['POST'])
def clear_test_report():
    """Clear the test report file."""
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)
        return jsonify({
            'status': 'ok',
            'message': 'Test report cleared'
        })
    return jsonify({
        'status': 'ok',
        'message': 'No report to clear'
    })

if __name__ == '__main__':
    port = int(os.environ.get('WEBUI_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
