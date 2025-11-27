"""
Test the multi-test case parsing logic
"""

import re

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

# Test with sample input
sample_instructions = """
Login with 'standard_user' and 'secret_sauce'.
Once on the Products page, find "Sauce Labs Backpack" and click 'ADD TO CART'.
Open the shopping cart icon in the top-right corner.
Verify that the backpack appears in the cart with the correct name and price.
TestCase Number - 1001.1.1.4, Add Single Product Test: Ensure individual products can be added successfully to the cart.
Tell us if this test case is passed or failed? Update the result in one word (Pass/Fail) in report against this test case number.

---

## Test Case 5: Add Multiple Products Test

**Test Case Number:** 1001.1.1.5  
**Description:** Add Multiple Products Test - Ensure multiple products can be added to cart simultaneously

**Steps:**
- Login with 'standard_user' and 'secret_sauce'
- Add "Sauce Labs Backpack" to the cart
- Add "Sauce Labs Bike Light" to the cart
- Add "Sauce Labs Bolt T-Shirt" to the cart
- Click on the cart icon to review added items
- Verify that all selected products are displayed with accurate names and prices

**Validation:**  
TestCase Number - 1001.1.1.5, Add Multiple Products Test: Ensure multiple products can be added to cart simultaneously.  
Tell us if this test case is passed or failed? Update the result in one word (Pass/Fail) in report against this test case number.
"""

test_cases = extract_all_testcases(sample_instructions)

print(f"\n{'='*70}")
print(f"Found {len(test_cases)} test cases:")
print(f"{'='*70}\n")

for i, tc in enumerate(test_cases, 1):
    print(f"{i}. Test Case: {tc['number']}")
    print(f"   Name: {tc['name']}")
    print(f"   Position: {tc['start_pos']}")
    print()

if len(test_cases) == 2:
    print("✅ TEST PASSED: Successfully detected both test cases!")
else:
    print(f"❌ TEST FAILED: Expected 2 test cases, found {len(test_cases)}")
