from playwright.sync_api import sync_playwright
from computers.default.local_playwright import LocalPlaywrightBrowser
from agent.agent import Agent
import argparse

def setup_login_automation():
    # Initialize the LocalPlaywrightBrowser
    computer = LocalPlaywrightBrowser(headless=False)
    
    # Initialize the Agent
    agent = Agent(computer=computer)
    
    return agent, computer

def add_smart_selectors(page):
    """Add helper functions to find elements using multiple selector strategies"""
    selectors = {
        'username': [
            '#user-name',                    # ID
            'input[name="user-name"]',       # Name attribute
            'input[data-test="username"]',   # Data attribute
            'input[type="text"]',            # Input type
            '//input[@placeholder="Username"]'  # XPath with placeholder
        ],
        'password': [
            '#password',                     # ID
            'input[name="password"]',        # Name attribute
            'input[data-test="password"]',   # Data attribute
            'input[type="password"]',        # Input type
            '//input[@placeholder="Password"]'  # XPath with placeholder
        ],
        'submit': [
            '#login-button',                 # ID
            'input[type="submit"]',          # Input type
            'button[type="submit"]',         # Button type
            '.btn_action',                   # Class
            '//button[contains(text(), "Login")]'  # XPath with text
        ]
    }
    
    def try_selectors(selector_list):
        for selector in selector_list:
            try:
                if selector.startswith('//'):
                    element = page.wait_for_selector(f"xpath={selector}", timeout=2000)
                else:
                    element = page.wait_for_selector(selector, timeout=2000)
                if element:
                    return element
            except:
                continue
        return None
    
    return try_selectors, selectors

def enhance_computer_capabilities(computer):
    """Add enhanced form interaction capabilities to the computer"""
    original_handle_command = computer._handle_command
    
    def enhanced_handle_command(command: str) -> list[dict]:
        # If it's a login-related command
        if "username" in command.lower() and "password" in command.lower():
            page = computer._page
            try_selectors, selectors = add_smart_selectors(page)
            
            # Extract username and password from command (you might want to enhance this)
            import re
            username_match = re.search(r"'([^']*)'.*username", command)
            password_match = re.search(r"'([^']*)'.*password", command)
            
            if username_match and password_match:
                username = username_match.group(1)
                password = password_match.group(1)
                
                # Try to fill the form using smart selectors
                username_element = try_selectors(selectors['username'])
                if username_element:
                    username_element.fill(username)
                
                password_element = try_selectors(selectors['password'])
                if password_element:
                    password_element.fill(password)
                
                submit_element = try_selectors(selectors['submit'])
                if submit_element:
                    submit_element.click()
                
                return [{"status": "success", "message": "Login form filled and submitted"}]
        
        # For all other commands, use the original handler
        return original_handle_command(command)
    
    # Replace the handle command method with our enhanced version
    computer._handle_command = enhanced_handle_command
    return computer

def main():
    parser = argparse.ArgumentParser(description='Web Login Automation Example')
    parser.add_argument('--url', default="https://www.saucedemo.com/v1/",
                      help='The URL to navigate to')
    parser.add_argument('--username', default="standard_user",
                      help='Username for login')
    parser.add_argument('--password', default="secret_sauce",
                      help='Password for login')
    args = parser.parse_args()

    # Setup the automation
    agent, computer = setup_login_automation()
    
    # Enhance the computer's capabilities
    computer = enhance_computer_capabilities(computer)
    
    # Navigate to the website
    computer.run_command(f"navigate to {args.url}")
    
    # Attempt login
    login_command = f"Enter '{args.username}' in the username field, then enter '{args.password}' in the password field and click the login button"
    result = computer.run_command(login_command)
    
    # Keep the browser open for observation
    import time
    time.sleep(5)

if __name__ == "__main__":
    main()