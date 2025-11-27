"""
Extract Screenshots from Test Case Report
Saves all screenshots from the JSON report to individual PNG files
"""

import json
import os
import base64
from datetime import datetime

REPORT_FILE = os.path.join(os.path.dirname(__file__), 'test_reports', 'test_case_report.json')
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), 'test_reports', 'screenshots')

def ensure_screenshots_directory():
    """Ensure the screenshots directory exists."""
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)
        print(f"✅ Created directory: {SCREENSHOTS_DIR}")

def extract_screenshots():
    """Extract all screenshots from the JSON report."""
    if not os.path.exists(REPORT_FILE):
        print(f"❌ Report file not found: {REPORT_FILE}")
        return
    
    # Load report
    with open(REPORT_FILE, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    test_cases = report.get('test_cases', [])
    
    if not test_cases:
        print("❌ No test cases found in report")
        return
    
    ensure_screenshots_directory()
    
    print(f"\n{'='*70}")
    print(f"  EXTRACTING SCREENSHOTS FROM TEST REPORT")
    print(f"{'='*70}\n")
    
    success_count = 0
    error_count = 0
    
    for i, tc in enumerate(test_cases, 1):
        test_number = tc.get('test_case_number', 'Unknown')
        test_name = tc.get('test_case_name', 'Unknown')
        executed_at = tc.get('executed_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        screenshot_data = tc.get('screenshot', '')
        
        print(f"{i}. Processing Test Case {test_number} - {test_name}")
        
        if not screenshot_data:
            print(f"   ⚠️  No screenshot data available")
            error_count += 1
            continue
        
        try:
            # Handle truncated screenshots (backward compatibility)
            if screenshot_data.endswith('...'):
                print(f"   ⚠️  Screenshot is truncated (old format), skipping")
                error_count += 1
                continue
            
            # Create safe filename
            safe_tc_number = test_number.replace('.', '_')
            safe_timestamp = executed_at.replace(':', '-').replace(' ', '_')
            screenshot_filename = f"TC_{safe_tc_number}_{safe_timestamp}.png"
            screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
            
            # Decode and save
            screenshot_bytes = base64.b64decode(screenshot_data)
            
            with open(screenshot_path, 'wb') as img_file:
                img_file.write(screenshot_bytes)
            
            file_size_kb = len(screenshot_bytes) / 1024
            print(f"   ✅ Saved: {screenshot_filename} ({file_size_kb:.1f} KB)")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            error_count += 1
    
    print(f"\n{'='*70}")
    print(f"  EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"\n✅ Successfully extracted: {success_count} screenshots")
    
    if error_count > 0:
        print(f"⚠️  Errors/Skipped: {error_count} screenshots")
    
    print(f"\n📁 Screenshots location: {SCREENSHOTS_DIR}")

if __name__ == '__main__':
    extract_screenshots()
