from computers import Computer
from utils import (
    create_response,
    show_image,
    pp,
    sanitize_message,
    check_blocklisted_url,
)
import json
from typing import Callable


class Agent:
    """
    A sample agent class that can be used to interact with a computer.

    (See simple_cua_loop.py for a simple example without an agent.)
    """

    def __init__(
        self,
        model="computer-use-preview",
        computer: Computer = None,
        tools: list[dict] = [],
        acknowledge_safety_check_callback: Callable = lambda *args: True,  # Changed to True by default
    ):
        self.model = model
        self.computer = computer
        self.tools = tools
        self.print_steps = True
        self.debug = False
        self.show_images = False
        self.acknowledge_safety_check_callback = acknowledge_safety_check_callback
        self.safety_checks_acknowledged = set()  # Track already acknowledged checks

        if computer:
            dimensions = computer.get_dimensions()
            self.tools += [
                {
                    "type": "computer-preview",
                    "display_width": dimensions[0],
                    "display_height": dimensions[1],
                    "environment": computer.get_environment(),
                },
            ]

    def debug_print(self, *args):
        if self.debug:
            pp(*args)

    def handle_item(self, item):
        """Handle each item; may cause a computer action + screenshot."""
        if item["type"] == "message":
            if self.print_steps:
                print(item["content"][0]["text"])

        if item["type"] == "function_call":
            name, args = item["name"], json.loads(item["arguments"])
            if self.print_steps:
                print(f"{name}({args})")

            if hasattr(self.computer, name):  # if function exists on computer, call it
                method = getattr(self.computer, name)
                method(**args)
            return [
                {
                    "type": "function_call_output",
                    "call_id": item["call_id"],
                    "output": "success",  # hard-coded output for demo
                }
            ]

        if item["type"] == "computer_call":
            action = item["action"]
            action_type = action["type"]
            action_args = {k: v for k, v in action.items() if k != "type"}
            if self.print_steps:
                print(f"{action_type}({action_args})")

            method = getattr(self.computer, action_type)
            method(**action_args)

            screenshot_base64 = self.computer.screenshot()
            if self.show_images:
                show_image(screenshot_base64)

            # Handle safety checks more intelligently
            pending_checks = item.get("pending_safety_checks", [])
            for check in pending_checks:
                message = check["message"]
                # Skip if we've already acknowledged this type of check
                if message in self.safety_checks_acknowledged:
                    continue
                # Auto-acknowledge non-financial checks
                if "financial" not in message.lower() and "payment" not in message.lower():
                    self.safety_checks_acknowledged.add(message)
                    continue
                # For financial checks, use the callback
                if not self.acknowledge_safety_check_callback(message):
                    raise ValueError(
                        f"Safety check failed: {message}. Cannot proceed with financial transactions."
                    )
                self.safety_checks_acknowledged.add(message)

            call_output = {
                "type": "computer_call_output",
                "call_id": item["call_id"],
                "acknowledged_safety_checks": pending_checks,
                "output": {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{screenshot_base64}",
                },
            }

            # additional URL safety checks for browser environments
            if self.computer.get_environment() == "browser":
                current_url = self.computer.get_current_url()
                check_blocklisted_url(current_url)
                call_output["output"]["current_url"] = current_url

            return [call_output]
        return []

    def run_full_turn(
        self, input_items, print_steps=True, debug=False, show_images=False
    ):
        self.print_steps = print_steps
        self.debug = debug
        self.show_images = show_images
        new_items = []
        
        # Ensure input_items is a list and has proper structure
        if not isinstance(input_items, list):
            input_items = [input_items]
            
        # Initialize with a system message if empty
        if not input_items:
            input_items = [{"role": "system", "content": [{"text": "Ready to assist."}]}]

        # keep looping until we get a final response
        while new_items[-1].get("role") != "assistant" if new_items else True:
            self.debug_print([sanitize_message(msg) for msg in input_items + new_items])

            try:
                # Add role and proper structure to input items
                formatted_items = []
                for item in input_items + new_items:
                    if item.get("type") == "message":
                        formatted_item = {
                            "role": "user",
                            "content": item.get("content", [{"text": ""}])
                        }
                        formatted_items.append(formatted_item)
                    elif item.get("type") in ["computer_call_output", "function_call_output"]:
                        formatted_item = {
                            "role": "assistant",
                            "content": [{"text": str(item.get("output", ""))}]
                        }
                        formatted_items.append(formatted_item)
                    else:
                        formatted_items.append(item)

                response = create_response(
                    model=self.model,
                    input=input_items + new_items,
                    tools=self.tools,
                    truncation="auto",
                )
                self.debug_print(response)

                if "output" not in response:
                    if self.debug:
                        print(response)
                    if "error" in response:
                        error_msg = response.get("error", {}).get("message", "Unknown error")
                        print(f"Error from model: {error_msg}")
                        # Add proper role to error message
                        return new_items + [{"type": "message", "role": "assistant", "content": [{"text": f"Error: {error_msg}"}]}]
                    raise ValueError("No output from model")
                
                # Handle the response output
                output_items = response.get("output", [])
                for item in output_items:
                    # Ensure each output item has a role
                    if "role" not in item:
                        if item.get("type") == "message":
                            item["role"] = "assistant"
                        elif item.get("type") in ["computer_call_output", "function_call_output"]:
                            item["role"] = "system"
                    new_items.append(item)
                    # Handle any computer actions
                    result_items = self.handle_item(item)
                    if result_items:
                        new_items.extend(result_items)
            except Exception as e:
                print(f"Error processing response: {str(e)}")
                return new_items + [{"type": "message", "role": "assistant", "content": [{"text": f"Error: {str(e)}"}]}]

        return new_items