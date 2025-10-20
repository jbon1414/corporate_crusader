import streamlit as st
from utils.auth import AuthManager

def test_auth():
    """Simple test page to debug authentication"""
    st.title("🔍 Authentication Debug Tool")
    
    auth_manager = AuthManager()
    
    st.header("Test Database Connection")
    try:
        # Test basic connection
        response = auth_manager.supabase_client.supabase.table("users").select("id, username, email").execute()
        st.success(f"✅ Database connected! Found {len(response.data)} users")
        
        # Show users (without passwords)
        if response.data:
            st.subheader("Users in database:")
            for user in response.data:
                st.write(f"- ID: {user.get('id')}, Username: {user.get('username')}, Email: {user.get('email')}")
        
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        return
    
    st.header("Test Authentication")
    
    with st.form("test_auth_form"):
        username_or_email = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Test Login")
        
        if submit and username_or_email and password:
            st.write("🔍 **Debug Information:**")
            
            # Test password hashing
            hashed_password = auth_manager.hash_password(password)
            st.write(f"Hashed password: {hashed_password}")
            
            # Test user lookup
            st.write(f"Looking for user: {username_or_email}")
            
            # Try username search
            try:
                response = auth_manager.supabase_client.supabase.table("users").select("*").eq("username", username_or_email).execute()
                st.write(f"Username search result: {len(response.data)} users found")
                if response.data:
                    user = response.data[0]
                    st.write(f"Found user by username: {user.get('username')} (ID: {user.get('id')})")
                    st.write(f"Stored password hash: {user.get('password')}")
                    st.write(f"Passwords match: {user.get('password') == hashed_password}")
            except Exception as e:
                st.error(f"Username search error: {str(e)}")
            
            # Try email search
            try:
                response = auth_manager.supabase_client.supabase.table("users").select("*").eq("email", username_or_email.lower()).execute()
                st.write(f"Email search result: {len(response.data)} users found")
                if response.data:
                    user = response.data[0]
                    st.write(f"Found user by email: {user.get('email')} (ID: {user.get('id')})")
                    st.write(f"Stored password hash: {user.get('password')}")
                    st.write(f"Passwords match: {user.get('password') == hashed_password}")
            except Exception as e:
                st.error(f"Email search error: {str(e)}")
            
            # Test full authentication
            st.write("**Full Authentication Test:**")
            success, user_data, message = auth_manager.authenticate_user(username_or_email, password)
            
            if success:
                st.success(f"✅ {message}")
                st.write("User data:", user_data)
            else:
                st.error(f"❌ {message}")

if __name__ == "__main__":
    test_auth()