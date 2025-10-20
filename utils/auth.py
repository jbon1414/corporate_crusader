import streamlit as st
import hashlib
import re
from typing import Optional, Dict, Tuple
from .supabase_conn import SupaBase
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

class AuthManager:
    def __init__(self):
        """Initialize the authentication manager."""
        self.supabase_client = SupaBase()
        # Migration is disabled since existing passwords are now properly hashed
        # self._migrate_plain_text_passwords()
        
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = "glenwood_social_app_salt_2024"  # In production, use a proper salt per user
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _migrate_plain_text_passwords(self):
        """Migrate any plain text passwords to hashed passwords."""
        try:
            # Get all users
            response = self.supabase_client.supabase.table("users").select("*").execute()
            
            for user in response.data:
                password = user.get('password', '')
                # Check if password is likely plain text (not a 64-character hex hash)
                if password and (len(password) != 64 or not all(c in '0123456789abcdef' for c in password.lower())):
                    # This looks like plain text, hash it
                    hashed_password = self.hash_password(password)
                    
                    # Update the user's password
                    self.supabase_client.supabase.table("users").update({
                        "password": hashed_password
                    }).eq("id", user['id']).execute()
                    
                    print(f"Migrated password for user: {user.get('username')}")
                    
        except Exception as e:
            print(f"Error during password migration: {str(e)}")
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        return True, "Password is valid"
    
    def check_username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        try:
            response = self.supabase_client.supabase.table("users").select("username").eq("username", username).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking username: {str(e)}")
            return False
    
    def check_email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        try:
            response = self.supabase_client.supabase.table("users").select("email").eq("email", email).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking email: {str(e)}")
            return False
    
    def create_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """Create a new user account."""
        # Validate inputs
        if not username or len(username.strip()) < 3:
            return False, "Username must be at least 3 characters long"
        
        if not self.validate_email(email):
            return False, "Please enter a valid email address"
        
        is_valid_password, password_message = self.validate_password(password)
        if not is_valid_password:
            return False, password_message
        
        # Check if username or email already exists
        if self.check_username_exists(username):
            return False, "Username already exists. Please choose a different one."
        
        if self.check_email_exists(email):
            return False, "Email already registered. Please use a different email or login."
        
        try:
            # Hash the password
            hashed_password = self.hash_password(password)
            
            # Create user data
            user_data = {
                "username": username.strip(),
                "email": email.strip().lower(),
                "password": hashed_password
            }
            
            # Insert into database
            response = self.supabase_client.supabase.table("users").insert(user_data).execute()
            
            if response.data:
                return True, "Account created successfully! You can now log in."
            else:
                return False, "Failed to create account. Please try again."
                
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return False, "An error occurred while creating your account. Please try again."
    
    def authenticate_user(self, username_or_email: str, password: str) -> Tuple[bool, Optional[Dict], str]:
        """Authenticate user with username/email and password."""
        if not username_or_email or not password:
            return False, None, "Please enter both username/email and password"
        
        try:
            # First, find the user by username or email
            user = None
            
            # Try to find by username first
            response = self.supabase_client.supabase.table("users").select("*").eq("username", username_or_email).execute()
            if response.data and len(response.data) > 0:
                user = response.data[0]
            else:
                # Try to find by email if username search failed
                response = self.supabase_client.supabase.table("users").select("*").eq("email", username_or_email.lower()).execute()
                if response.data and len(response.data) > 0:
                    user = response.data[0]
            
            if not user:
                return False, None, "Invalid username/email or password"
            
            # Now check if the password matches
            hashed_password = self.hash_password(password)
            stored_password = user['password']
            
            # Check if passwords match (try hashed first, then plain text for migration)
            if stored_password == hashed_password:
                # Password matches (properly hashed)
                user_safe = {k: v for k, v in user.items() if k != 'password'}
                return True, user_safe, "Login successful!"
            elif stored_password == password:
                # Password matches but was stored as plain text - migrate it
                self.supabase_client.supabase.table("users").update({
                    "password": hashed_password
                }).eq("id", user['id']).execute()
                
                user_safe = {k: v for k, v in user.items() if k != 'password'}
                return True, user_safe, "Login successful!"
            else:
                return False, None, "Invalid username/email or password"
                
        except Exception as e:
            print(f"Error authenticating user: {str(e)}")
            return False, None, "An error occurred during login. Please try again."
    
    def generate_reset_token(self, email: str) -> Tuple[bool, str]:
        """Generate a password reset token for the user."""
        if not self.validate_email(email):
            return False, "Please enter a valid email address"
        
        try:
            # Check if email exists
            if not self.check_email_exists(email):
                return False, "Email not found in our system"
            
            # Generate a secure reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Store the reset token in the database (you might want to add a reset_tokens table)
            # For now, we'll store it in session state as a simple implementation
            if 'reset_tokens' not in st.session_state:
                st.session_state.reset_tokens = {}
            
            st.session_state.reset_tokens[email] = {
                'token': reset_token,
                'expires': datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
            }
            
            # In a real application, you would send this token via email
            # For demo purposes, we'll just return it
            return True, f"Reset token generated: {reset_token}\n(In production, this would be sent to your email)"
            
        except Exception as e:
            print(f"Error generating reset token: {str(e)}")
            return False, "An error occurred while generating reset token"
    
    def reset_password(self, email: str, reset_token: str, new_password: str) -> Tuple[bool, str]:
        """Reset user password using reset token."""
        # Validate new password
        is_valid_password, password_message = self.validate_password(new_password)
        if not is_valid_password:
            return False, password_message
        
        try:
            # Check if reset token exists and is valid
            if ('reset_tokens' not in st.session_state or 
                email not in st.session_state.reset_tokens):
                return False, "Invalid or expired reset token"
            
            token_data = st.session_state.reset_tokens[email]
            
            # Check if token matches and hasn't expired
            if (token_data['token'] != reset_token or 
                datetime.now() > token_data['expires']):
                return False, "Invalid or expired reset token"
            
            # Hash the new password
            hashed_password = self.hash_password(new_password)
            
            # Update password in database
            response = self.supabase_client.supabase.table("users").update({
                "password": hashed_password
            }).eq("email", email).execute()
            
            if response.data:
                # Remove used reset token
                del st.session_state.reset_tokens[email]
                return True, "Password reset successfully! You can now log in with your new password."
            else:
                return False, "Failed to reset password. Please try again."
                
        except Exception as e:
            print(f"Error resetting password: {str(e)}")
            return False, "An error occurred while resetting password"
    
    def logout(self):
        """Log out the current user."""
        # Clear all authentication-related session state
        keys_to_clear = ['authenticated', 'user_data', 'user_id', 'username', 'brands']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return st.session_state.get('authenticated', False) and st.session_state.get('user_data') is not None
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user data."""
        if self.is_authenticated():
            return st.session_state.get('user_data')
        return None
    
    def require_authentication(self):
        """Decorator/function to require authentication for app access."""
        if not self.is_authenticated():
            st.warning("⚠️ Please log in to access the application.")
            st.stop()