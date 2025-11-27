"""
Test Case Report Viewer
View and analyze test case execution reports
"""

import json
import os
from datetime import datetime

REPORT_FILE = os.path.join(os.path.dirname(__file__), 'test_reports', 'test_case_report.json')

def load_report():
    """Load the test report from JSON file."""
    if not os.path.exists(REPORT_FILE):
        print("❌ No test report found!")
        print(f"Expected location: {REPORT_FILE}")
        return None
    
    with open(REPORT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def display_summary(report):
    """Display summary statistics."""
    print("\n" + "="*80)
    print(f"  TEST SUITE: {report.get('test_suite', 'Unknown')}")
    print(f"  EXECUTION DATE: {report.get('execution_date', 'Unknown')}")
    print("="*80)
    
    summary = report.get('summary', {})
    total = summary.get('total_tests', 0)
    passed = summary.get('passed', 0)
    failed = summary.get('failed', 0)
    unknown = summary.get('unknown', 0)
    pass_rate = summary.get('pass_rate', '0%')
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total Tests: {total}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ❔ Unknown: {unknown}")
    print(f"   Pass Rate: {pass_rate}")
    print()

def display_detailed_results(report):
    """Display detailed test case results."""
    test_cases = report.get('test_cases', [])
    
    if not test_cases:
        print("No test cases executed yet.")
        return
    
    print("\n" + "="*80)
    print("  DETAILED TEST RESULTS")
    print("="*80 + "\n")
    
    for i, tc in enumerate(test_cases, 1):
        result_symbol = "✅" if tc['result'] == 'Pass' else "❌" if tc['result'] == 'Fail' else "❔"
        
        print(f"{i}. {result_symbol} Test Case: {tc['test_case_number']}")
        print(f"   Name: {tc['test_case_name']}")
        print(f"   Result: {tc['result']}")
        print(f"   Executed: {tc['executed_at']}")
        
        # Show terminal output summary (first 200 chars)
        terminal_out = tc.get('terminal_output', '')
        if terminal_out:
            terminal_summary = terminal_out[:200] + "..." if len(terminal_out) > 200 else terminal_out
            print(f"   Output: {terminal_summary}")
        
        print()

def display_failed_tests(report):
    """Display only failed test cases."""
    test_cases = report.get('test_cases', [])
    failed_tests = [tc for tc in test_cases if tc['result'] == 'Fail']
    
    if not failed_tests:
        print("\n✅ No failed tests! All tests passed.")
        return
    
    print("\n" + "="*80)
    print(f"  FAILED TESTS ({len(failed_tests)} total)")
    print("="*80 + "\n")
    
    for i, tc in enumerate(failed_tests, 1):
        print(f"{i}. ❌ Test Case: {tc['test_case_number']}")
        print(f"   Name: {tc['test_case_name']}")
        print(f"   Executed: {tc['executed_at']}")
        print(f"   Output: {tc.get('terminal_output', 'No output')[:200]}")
        print()

def export_csv_report(report, output_file='test_report.csv'):
    """Export test results to CSV format with screenshots saved as separate files."""
    import csv
    import base64
    
    test_cases = report.get('test_cases', [])
    
    # Create screenshots directory
    screenshots_dir = os.path.join(os.path.dirname(output_file), 'screenshots')
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Test Case Number', 'Test Case Name', 'Result', 'Executed At', 'Terminal Output', 'Screenshot File'])
        
        for tc in test_cases:
            # Save screenshot if available
            screenshot_file = ''
            screenshot_data = tc.get('screenshot', '')
            
            if screenshot_data:
                # Handle both truncated and full screenshots
                # Remove the "..." suffix if present
                if screenshot_data.endswith('...'):
                    screenshot_data = screenshot_data[:-3]
                
                try:
                    # Create filename from test case number
                    safe_tc_number = tc['test_case_number'].replace('.', '_')
                    screenshot_filename = f"TC_{safe_tc_number}_{tc['executed_at'].replace(':', '-').replace(' ', '_')}.png"
                    screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                    
                    # Decode and save screenshot
                    screenshot_bytes = base64.b64decode(screenshot_data)
                    with open(screenshot_path, 'wb') as img_file:
                        img_file.write(screenshot_bytes)
                    
                    screenshot_file = screenshot_filename
                    print(f"  Saved screenshot: {screenshot_filename}")
                except Exception as e:
                    print(f"  ⚠️  Could not save screenshot for {tc['test_case_number']}: {e}")
                    screenshot_file = 'Error saving screenshot'
            
            writer.writerow([
                tc['test_case_number'],
                tc['test_case_name'],
                tc['result'],
                tc['executed_at'],
                tc.get('terminal_output', '')[:500],  # Truncate for CSV
                screenshot_file
            ])
    
    print(f"\n✅ Report exported to: {output_file}")
    print(f"✅ Screenshots saved to: {screenshots_dir}")

def main():
    """Main function to display test report."""
    report = load_report()
    
    if not report:
        return
    
    # Display summary
    display_summary(report)
    
    # Display detailed results
    display_detailed_results(report)
    
    # Display failed tests
    display_failed_tests(report)
    
    # Option to export
    print("\n" + "="*80)
    export_choice = input("Would you like to export the report to CSV? (y/n): ").strip().lower()
    
    if export_choice == 'y':
        csv_file = os.path.join(os.path.dirname(REPORT_FILE), 'test_report.csv')
        export_csv_report(report, csv_file)

if __name__ == '__main__':
    main()
