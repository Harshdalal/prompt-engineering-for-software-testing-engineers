def check_password_strength(password):
    """
    Checks if password is strong enough
    Rules: minimum 8 characters
    """
    if len(password) >= 8:
        return "Strong"
    return "Weak"


def login_user(username, password):
    """
    Simple login function
    Returns True if login successful
    """
    if username == "admin" and password == "admin123":
        return True
    return False