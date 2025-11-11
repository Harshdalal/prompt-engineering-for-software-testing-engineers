# user_registration.py

def register_user(username, email, age, password):
    """
    Register new user
    Requirements:
    - Username: 3-20 characters, alphanumeric only
    - Email: valid format with @ and domain
    - Age: 18-100
    - Password: minimum 8 characters, must contain number
    """
    if len(username) < 3 or len(username) > 20:
        return "Invalid username length"
    if not username.isalnum():
        return "Username must be alphanumeric"
    if "@" not in email or "." not in email:
        return "Invalid email format"
    if age < 18 or age > 100:
        return "Invalid age"
    if len(password) < 8:
        return "Password too short"
    if not any(char.isdigit() for char in password):
        return "Password must contain number"
    return "Registration successful"