import streamlit as st
from .auth import AuthManager

def render_auth_ui():
    """Render the authentication UI with login/signup/reset password options."""
    
    # Initialize auth manager
    auth_manager = AuthManager()
    
    # Create tabs for different auth actions
    tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Sign Up", "🔄 Reset Password"])
    
    with tab1:
        render_login_form(auth_manager)
    
    with tab2:
        render_signup_form(auth_manager)
    
    with tab3:
        render_reset_password_form(auth_manager)

def render_login_form(auth_manager):
    """Render the login form."""
    st.subheader("Welcome Back!")
    st.write("Sign in to your account to continue")
    
    with st.form("login_form"):
        username_or_email = st.text_input("Username or Email", placeholder="Enter your username or email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submit_button = st.form_submit_button("🔓 Log In", use_container_width=True)
        
        if submit_button:
            if username_or_email and password:
                with st.spinner("Authenticating..."):
                    success, user_data, message = auth_manager.authenticate_user(username_or_email, password)
                
                if success:
                    # Set session state for authenticated user
                    st.session_state.authenticated = True
                    st.session_state.user_data = user_data
                    st.session_state.user_id = user_data['id']
                    st.session_state.username = user_data['username']
                    
                    # Clear any cached data to reload user-specific data
                    if 'brands' in st.session_state:
                        del st.session_state.brands
                    
                    st.success(f"Welcome back, {user_data['username']}!")
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please fill in all fields")

def render_signup_form(auth_manager):
    """Render the signup form."""
    st.subheader("Create Your Account")
    st.write("Join us to start creating amazing social media content!")
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", placeholder="Choose a username (min 3 characters)")
        
        with col2:
            email = st.text_input("Email", placeholder="Enter your email address")
        
        password = st.text_input("Password", type="password", placeholder="Create a strong password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        # Password requirements info
        st.info("📋 **Password Requirements:**\n"
               "• At least 8 characters long\n"
               "• Contains uppercase and lowercase letters\n"
               "• Contains at least one number")
        
        agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        submit_button = st.form_submit_button("🎉 Create Account", use_container_width=True)
        
        if submit_button:
            if not all([username, email, password, confirm_password]):
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif not agree_terms:
                st.error("Please agree to the Terms of Service and Privacy Policy")
            else:
                with st.spinner("Creating your account..."):
                    success, message = auth_manager.create_user(username, email, password)
                
                if success:
                    st.success(message)
                    st.info("👆 Switch to the Login tab to sign in with your new account!")
                else:
                    st.error(message)

def render_reset_password_form(auth_manager):
    """Render the password reset form."""
    st.subheader("Reset Your Password")
    st.write("Enter your email to receive a password reset token")
    
    if 'reset_step' not in st.session_state:
        st.session_state.reset_step = 1
    
    if st.session_state.reset_step == 1:
        # Step 1: Request reset token
        with st.form("reset_request_form"):
            email = st.text_input("Email Address", placeholder="Enter the email associated with your account")
            
            submit_button = st.form_submit_button("🔄 Send Reset Token", use_container_width=True)
            
            if submit_button:
                if email:
                    with st.spinner("Generating reset token..."):
                        success, message = auth_manager.generate_reset_token(email)
                    
                    if success:
                        st.session_state.reset_email = email
                        st.session_state.reset_step = 2
                        st.success("Reset token generated!")
                        st.info(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter your email address")
    
    elif st.session_state.reset_step == 2:
        # Step 2: Enter token and new password
        st.info(f"📧 Reset token has been generated for: {st.session_state.reset_email}")
        
        with st.form("reset_password_form"):
            reset_token = st.text_input("Reset Token", placeholder="Enter the reset token")
            new_password = st.text_input("New Password", type="password", placeholder="Enter your new password")
            confirm_new_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm your new password")
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit_button = st.form_submit_button("🔑 Reset Password", use_container_width=True)
            
            with col2:
                cancel_button = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if cancel_button:
                st.session_state.reset_step = 1
                if 'reset_email' in st.session_state:
                    del st.session_state.reset_email
                st.rerun()
            
            if submit_button:
                if not all([reset_token, new_password, confirm_new_password]):
                    st.error("Please fill in all fields")
                elif new_password != confirm_new_password:
                    st.error("Passwords do not match")
                else:
                    with st.spinner("Resetting password..."):
                        success, message = auth_manager.reset_password(
                            st.session_state.reset_email, 
                            reset_token, 
                            new_password
                        )
                    
                    if success:
                        st.success(message)
                        st.session_state.reset_step = 1
                        if 'reset_email' in st.session_state:
                            del st.session_state.reset_email
                        st.info("👆 Switch to the Login tab to sign in with your new password!")
                    else:
                        st.error(message)

def render_user_menu():
    """Render the user menu for authenticated users."""
    auth_manager = AuthManager()
    user = auth_manager.get_current_user()
    
    if user:
        with st.sidebar:
            st.write("---")
            st.write(f"👋 **Welcome, {user['username']}!**")
            st.write(f"📧 {user['email']}")
            
            if st.button("🚪 Logout", use_container_width=True):
                auth_manager.logout()
                st.success("You have been logged out successfully!")
                st.rerun()

def check_authentication():
    """Check if user is authenticated and handle accordingly."""
    auth_manager = AuthManager()
    
    if not auth_manager.is_authenticated():
        # Show login/signup interface
        st.title("🎨 Social Media Content Generator")
        st.write("Create engaging social media content with AI assistance")
        st.write("---")
        
        render_auth_ui()
        return False
    else:
        # User is authenticated, show user menu
        render_user_menu()
        return True