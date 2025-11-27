def log_action(action: str, details: str = None):
    """Log a computer action with optional details"""
    message = f"[Computer Action] {action}"
    if details:
        message += f": {details}"
    print(message)