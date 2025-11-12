# demo_api_endpoints.py

"""
User Management API
Simple RESTful API for user operations
"""

users = {}
sessions = {}
user_counter = 1000


def validate_email(email):
    """Check if email format is valid"""
    return email and "@" in email and "." in email


def validate_password(password):
    """Check password strength"""
    if not password or len(password) < 8:
        return False
    
    has_digit = any(c.isdigit() for c in password)
    has_upper = any(c.isupper() for c in password)
    
    return has_digit and has_upper


def create_user(username, email, password, role="user"):
    """POST /api/users - Create new user"""
    global user_counter
    
    # Validate username
    if not username or len(username) < 3 or len(username) > 20:
        return {"success": False, "error": "Username must be 3-20 characters"}
    
    if username in users:
        return {"success": False, "error": "Username already exists"}
    
    # Validate email
    if not validate_email(email):
        return {"success": False, "error": "Invalid email format"}
    
    # Check duplicate email
    for user in users.values():
        if user["email"] == email:
            return {"success": False, "error": "Email already registered"}
    
    # Validate password
    if not validate_password(password):
        return {"success": False, "error": "Password must be 8+ characters with number and uppercase"}
    
    # Validate role
    if role not in ["user", "admin"]:
        return {"success": False, "error": "Role must be user or admin"}
    
    # Create user
    user_counter += 1
    user_id = user_counter
    
    user = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "password": password,
        "role": role,
        "status": "active"
    }
    
    users[username] = user
    
    return {"success": True, "user_id": user_id, "username": username, "role": role}


def login_user(username, password):
    """POST /api/auth/login - Authenticate user"""
    if not username or not password:
        return {"success": False, "error": "Username and password required"}
    
    if username not in users:
        return {"success": False, "error": "Invalid credentials"}
    
    user = users[username]
    
    if user["password"] != password:
        return {"success": False, "error": "Invalid credentials"}
    
    if user["status"] != "active":
        return {"success": False, "error": "Account inactive"}
    
    # Create session
    session_token = f"TOKEN_{user['user_id']}_{len(sessions) + 1}"
    sessions[session_token] = {
        "user_id": user["user_id"],
        "username": username,
        "role": user["role"]
    }
    
    return {"success": True, "session_token": session_token, "user_id": user["user_id"]}


def get_user(session_token, username):
    """GET /api/users/{username} - Get user details"""
    if not session_token or session_token not in sessions:
        return {"success": False, "error": "Unauthorized"}
    
    if username not in users:
        return {"success": False, "error": "User not found"}
    
    session = sessions[session_token]
    user = users[username]
    
    # Users can only view themselves unless admin
    if session["username"] != username and session["role"] != "admin":
        return {"success": False, "error": "Forbidden"}
    
    return {
        "success": True,
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "status": user["status"]
        }
    }


def update_user(session_token, username, new_email=None, new_password=None):
    """PUT /api/users/{username} - Update user info"""
    if not session_token or session_token not in sessions:
        return {"success": False, "error": "Unauthorized"}
    
    if username not in users:
        return {"success": False, "error": "User not found"}
    
    session = sessions[session_token]
    
    # Users can only update themselves
    if session["username"] != username:
        return {"success": False, "error": "Forbidden"}
    
    user = users[username]
    
    # Update email
    if new_email:
        if not validate_email(new_email):
            return {"success": False, "error": "Invalid email format"}
        user["email"] = new_email
    
    # Update password
    if new_password:
        if not validate_password(new_password):
            return {"success": False, "error": "Password must be 8+ characters with number and uppercase"}
        user["password"] = new_password
    
    return {"success": True, "message": "User updated successfully"}


def delete_user(session_token, username):
    """DELETE /api/users/{username} - Delete user"""
    if not session_token or session_token not in sessions:
        return {"success": False, "error": "Unauthorized"}
    
    if username not in users:
        return {"success": False, "error": "User not found"}
    
    session = sessions[session_token]
    
    # Only admins can delete users
    if session["role"] != "admin":
        return {"success": False, "error": "Forbidden - Admin only"}
    
    # Delete user and their sessions
    user_id = users[username]["user_id"]
    del users[username]
    
    # Remove user sessions
    sessions_to_remove = [token for token, sess in sessions.items() if sess["user_id"] == user_id]
    for token in sessions_to_remove:
        del sessions[token]
    
    return {"success": True, "message": f"User {username} deleted"}