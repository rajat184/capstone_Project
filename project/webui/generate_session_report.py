#!/usr/bin/env python3
"""
Generate HTML Report for Last Test Session
Creates a professional, presentable HTML report showing ALL test cases from the most recent test execution session.
"""

import json
import os
from datetime import datetime

def generate_html_report(json_file_path, output_html_path=None):
    """
    Generate HTML report for all test cases from the last session in the JSON report file.
    
    Args:
        json_file_path: Path to test_case_report.json
        output_html_path: Optional path for output HTML file (default: last_session_report.html)
    """
    # Read the JSON report
    with open(json_file_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    # Get all test cases from the current session
    if not report_data.get('test_cases'):
        print("No test cases found in the report.")
        return
    
    test_cases = report_data['test_cases']
    session_id = report_data.get('session_id', 'Unknown')
    execution_date = report_data.get('execution_date', 'Unknown')
    summary = report_data.get('summary', {})
    
    # Determine output path
    if output_html_path is None:
        output_html_path = os.path.join(
            os.path.dirname(json_file_path),
            'last_session_report.html'
        )
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Session Report - {session_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .session-info {{
            font-size: 1em;
            opacity: 0.9;
            margin-top: 15px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        
        .summary-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .summary-card .label {{
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: 700;
            color: #212529;
        }}
        
        .summary-card.passed .value {{
            color: #10b981;
        }}
        
        .summary-card.failed .value {{
            color: #ef4444;
        }}
        
        .summary-card.unknown .value {{
            color: #f59e0b;
        }}
        
        .test-cases {{
            padding: 40px;
        }}
        
        .test-case {{
            background: #ffffff;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 30px;
            overflow: hidden;
            transition: all 0.3s;
        }}
        
        .test-case:hover {{
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        
        .test-case-header {{
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e5e7eb;
            cursor: pointer;
        }}
        
        .test-case-header:hover {{
            background: #f9fafb;
        }}
        
        .test-case-title {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .test-case-number {{
            background: #667eea;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .test-case-name {{
            font-size: 1.2em;
            font-weight: 600;
            color: #1f2937;
        }}
        
        .status-badge {{
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.95em;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        
        .status-badge.pass {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .status-badge.fail {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .status-badge.unknown {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .test-case-body {{
            padding: 30px;
            display: none;
        }}
        
        .test-case-body.expanded {{
            display: block;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #374151;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        .meta-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .meta-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .meta-label {{
            font-size: 0.85em;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        
        .meta-value {{
            font-size: 1em;
            color: #1f2937;
            font-weight: 500;
        }}
        
        .instructions {{
            background: #f9fafb;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 4px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.6;
            color: #374151;
        }}
        
        .terminal-output {{
            background: #1f2937;
            color: #10b981;
            padding: 20px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .screenshot {{
            text-align: center;
            margin-top: 20px;
        }}
        
        .screenshot img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            border: 1px solid #e5e7eb;
        }}
        
        .expand-icon {{
            transition: transform 0.3s;
            font-size: 1.2em;
            color: #6b7280;
        }}
        
        .test-case-header.expanded .expand-icon {{
            transform: rotate(180deg);
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f9fafb;
            color: #6b7280;
            font-size: 0.9em;
            border-top: 2px solid #e5e7eb;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
            .test-case {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test Execution Report</h1>
            <div class="session-info">
                <strong>Session ID:</strong> {session_id}<br>
                <strong>Execution Date:</strong> {execution_date}
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="label">Total Tests</div>
                <div class="value">{summary.get('total_tests', len(test_cases))}</div>
            </div>
            <div class="summary-card passed">
                <div class="label">Passed</div>
                <div class="value">{summary.get('passed', 0)}</div>
            </div>
            <div class="summary-card failed">
                <div class="label">Failed</div>
                <div class="value">{summary.get('failed', 0)}</div>
            </div>
            <div class="summary-card unknown">
                <div class="label">Unknown</div>
                <div class="value">{summary.get('unknown', 0)}</div>
            </div>
            <div class="summary-card">
                <div class="label">Pass Rate</div>
                <div class="value">{summary.get('pass_rate', '0%')}</div>
            </div>
        </div>
        
        <div class="test-cases">
"""
    
    # Add each test case
    for idx, test_case in enumerate(test_cases, 1):
        test_number = test_case.get('test_case_number', f'TC-{idx}')
        test_name = test_case.get('test_case_name', 'Unnamed Test')
        result = test_case.get('result', 'Unknown')
        executed_at = test_case.get('executed_at', 'Unknown')
        instructions = test_case.get('instructions', 'No instructions provided')
        terminal_output = test_case.get('terminal_output', 'No output available')
        screenshot = test_case.get('screenshot', '')
        
        # Determine status styling
        status_class = result.lower()
        status_icon = '✓' if result == 'Pass' else '✗' if result == 'Fail' else '?'
        
        html_content += f"""
            <div class="test-case">
                <div class="test-case-header" onclick="toggleTestCase(this)">
                    <div class="test-case-title">
                        <span class="test-case-number">{test_number}</span>
                        <span class="test-case-name">{test_name}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span class="status-badge {status_class}">
                            <span>{status_icon}</span>
                            <span>{result}</span>
                        </span>
                        <span class="expand-icon">▼</span>
                    </div>
                </div>
                
                <div class="test-case-body">
                    <div class="meta-info">
                        <div class="meta-item">
                            <span class="meta-label">Test Case Number</span>
                            <span class="meta-value">{test_number}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Executed At</span>
                            <span class="meta-value">{executed_at}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Result</span>
                            <span class="meta-value" style="color: {'#10b981' if result == 'Pass' else '#ef4444' if result == 'Fail' else '#f59e0b'};">{result}</span>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">📋 Test Instructions</div>
                        <div class="instructions">{instructions}</div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">💻 Terminal Output</div>
                        <div class="terminal-output">{terminal_output}</div>
                    </div>
"""
        
        if screenshot:
            html_content += f"""
                    <div class="section">
                        <div class="section-title">📸 Screenshot</div>
                        <div class="screenshot">
                            <img src="data:image/png;base64,{screenshot}" alt="Test Screenshot">
                        </div>
                    </div>
"""
        
        html_content += """
                </div>
            </div>
"""
    
    # Close HTML
    html_content += f"""
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            Total Test Cases: {len(test_cases)} | 
            Session: {session_id}
        </div>
    </div>
    
    <script>
        function toggleTestCase(header) {{
            header.classList.toggle('expanded');
            const body = header.nextElementSibling;
            body.classList.toggle('expanded');
        }}
        
        // Expand the first test case by default
        document.addEventListener('DOMContentLoaded', function() {{
            const firstHeader = document.querySelector('.test-case-header');
            if (firstHeader) {{
                toggleTestCase(firstHeader);
            }}
        }});
    </script>
</body>
</html>
"""
    
    # Write the HTML file
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML report generated successfully!")
    print(f"  Session: {session_id}")
    print(f"  Test Cases: {len(test_cases)}")
    print(f"  Output: {output_html_path}")
    
    return output_html_path


def main():
    """Main function to generate the report."""
    # Default paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(script_dir, 'test_reports', 'test_case_report.json')
    
    if not os.path.exists(json_file):
        print(f"Error: Test report file not found at {json_file}")
        return
    
    # Generate the report
    output_file = generate_html_report(json_file)
    
    # Open in browser (optional)
    try:
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(output_file)}')
        print(f"✓ Report opened in browser")
    except Exception as e:
        print(f"Note: Could not auto-open browser: {e}")


if __name__ == '__main__':
    main()
