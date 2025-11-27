## Test Case 1: Valid Login Test

**Test Case Number:** 1001.1.1.1  
**Description:** Valid Login Test - Verify that a valid user can log in successfully

**Steps:**
- Load https://www.saucedemo.com/
- When the login page appears, type the username 'standard_user' in the username feild
- Type the password 'secret_sauce'
- Click on the Login button
- Wait for the Products page to fully load
- Verify that the header "Products" appears correctly
- Verify that all items are visible

**Validation:**  
TestCase Number - 1001.1.1.1, Valid Login Test: Verify that a valid user can log in successfully.  
Tell us if this test case is passed or failed? Update the result in one word (Pass/Fail) in report against this test case number.

---

## Test Case 2: Invalid Password Test

**Test Case Number:** 1001.1.1.2  
**Description:** Invalid Password Test - Ensure incorrect credentials produce an appropriate error message

**Steps:**
- Load https://www.saucedemo.com/
- Logout if login already by clicking on hamburger menu. When the login page appears, type the username 'standard_user' in the username feild
- Enter an incorrect password such as 'wrong_pass'
- Click on the Login button
- Observe the result
- Verify that an error message appears: "Epic sadface: Username and password do not match any user in this service"

**Validation:**  
TestCase Number - 1001.1.1.2, Invalid Password Test: Ensure incorrect credentials produce an appropriate error message.  
Tell us if this test case is passed or failed? Update the result in one word (Pass/Fail) in report against this test case number.

---

## Test Case 3: Blank Login Fields Test

**Test Case Number:** 1001.1.1.3  
**Description:** Blank Login Fields Test - Verify that empty fields trigger validation errors

**Steps:**
- Load https://www.saucedemo.com/
- Leave both Username and Password fields blank
- Click on the Login button
- Check if an error message appears indicating that the username is required

**Validation:**  
TestCase Number - 1001.1.1.3, Blank Login Fields Test: Verify that empty fields trigger validation errors.  
Tell us if this test case is passed or failed? Update the result in one word (Pass/Fail) in report against this test case number.

---

## Test Case 4: Add Single Product Test

**Test Case Number:** 1001.1.1.4  
**Description:** Add Single Product Test - Ensure individual products can be added successfully to the cart

**Steps:**
- Login using 'standard_user' as username and 'secret_sauce' as password
- Once on the Products page, find "Sauce Labs Backpack"
- Click 'ADD TO CART' for the backpack
- Open the shopping cart icon in the top-right corner
- Verify that the backpack appears in the cart with the correct name and price

**Validation:**  
TestCase Number - 1001.1.1.4, Add Single Product Test: Ensure individual products can be added successfully to the cart.  
Tell us if this test case is passed or failed? Update the result in one word (Pass/Fail) in report against this test case number.