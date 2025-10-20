from supabase import create_client, Client
from supabase.client import ClientOptions
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

# Load environment variables from .env
load_dotenv()

class SupaBase:
    def __init__(self):
        """
        Initialize the Supabase client options.
        """
        url = st.secrets["DATABASE_URL"]#os.environ.get("DATABASE_URL")
        key = st.secrets["SUPABASE_SECRET"]#os.environ.get("SUPABASE_SECRET")
        self.supabase = create_client(url, key)

    def get_brands(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch brands from the Supabase database, optionally filtered by user_id.
        Args:
            user_id: Optional user ID to filter brands by
        Returns:
            List of brand dictionaries
        """
        try:
            if user_id:
                response = self.supabase.table("brands").select("*").eq("user_id", user_id).execute()
            else:
                response = self.supabase.table("brands").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error fetching brands: {str(e)}")
            return []

    def get_brand_by_id(self, brand_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch a specific brand by ID, optionally filtered by user_id.
        Args:
            brand_id: UUID string of the brand
            user_id: Optional user ID to ensure brand ownership
        Returns:
            Brand dictionary or None if not found
        """
        try:
            query = self.supabase.table("brands").select("*").eq("id", brand_id)
            if user_id:
                query = query.eq("user_id", user_id)
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching brand by ID {brand_id}: {str(e)}")
            return None

    def create_brand(self, brand_data: Dict) -> Optional[Dict]:
        """
        Create a new brand in the database.
        Args:
            brand_data: Dictionary containing brand information
        Returns:
            Created brand dictionary or None if failed
        """
        try:
            # Add created_at and updated_at timestamps
            brand_data["created_at"] = datetime.now().isoformat()
            brand_data["updated_at"] = datetime.now().isoformat()
            
            response = self.supabase.table("brands").insert(brand_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating brand: {str(e)}")
            return None

    def update_brand(self, brand_id: str, brand_data: Dict) -> Optional[Dict]:
        """
        Update an existing brand in the database.
        Args:
            brand_id: UUID string of the brand to update
            brand_data: Dictionary containing updated brand information
        Returns:
            Updated brand dictionary or None if failed
        """
        try:
            # Add updated_at timestamp
            brand_data["updated_at"] = datetime.now().isoformat()
            
            response = self.supabase.table("brands").update(brand_data).eq("id", brand_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating brand {brand_id}: {str(e)}")
            return None

    def delete_brand(self, brand_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a brand from the database.
        Args:
            brand_id: UUID string of the brand to delete
            user_id: Optional user ID to ensure brand ownership
        Returns:
            True if successful, False otherwise
        """
        try:
            query = self.supabase.table("brands").delete().eq("id", brand_id)
            if user_id:
                query = query.eq("user_id", user_id)
            response = query.execute()
            return True
        except Exception as e:
            print(f"Error deleting brand {brand_id}: {str(e)}")
            return False

    def save_posts(self, brand_id: str, post: str, user_id: str, graphic_concept: str, type: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Save a post to the 'posts' table.
        Args:
            brand_id: UUID string of the brand
            post: Text/content of the post
            user_id: UUID string of the user
            graphic_concept: Description or identifier for the graphic concept
            type: Type of the post
            date: Optional ISO date string; if not provided, uses current datetime
        Returns:
            Created post dictionary or None if failed
        """
        try:
            post_data = {
                "brand_id": brand_id,
                "user_id": user_id,
                "post": post,
                "graphic_concept": graphic_concept,
                "type": type,
                "date": date 
            }
            response = self.supabase.table("posts").insert(post_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error saving post for brand {brand_id}: {str(e)}")
            return None

    def get_posts_by_brand(self, brand_id: str, user_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch all posts for a specific brand from the 'posts' table.
        Args:
            brand_id: UUID string of the brand
            user_id: Optional user ID to ensure access to posts
        Returns:
            List of post dictionaries
        """
        try:
            query = self.supabase.table("posts").select("*").eq("brand_id", brand_id)
            if user_id:
                query = query.eq("user_id", user_id)
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error fetching posts for brand {brand_id}: {str(e)}")
            return []

    # User management methods for authentication
    def create_user(self, username: str, email: str, password_hash: str) -> Optional[Dict]:
        """
        Create a new user in the database.
        Args:
            username: Username for the user
            email: Email address
            password_hash: Hashed password
        Returns:
            User dictionary or None if failed
        """
        try:
            user_data = {
                "username": username,
                "email": email,
                "password": password_hash
            }
            response = self.supabase.table("users").insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return None

    def get_user_by_username_or_email(self, username_or_email: str) -> Optional[Dict]:
        """
        Fetch user by username or email.
        Args:
            username_or_email: Username or email to search for
        Returns:
            User dictionary or None if not found
        """
        try:
            # Try username first
            response = self.supabase.table("users").select("*").eq("username", username_or_email).execute()
            if response.data:
                return response.data[0]
            
            # Try email if username search failed
            response = self.supabase.table("users").select("*").eq("email", username_or_email.lower()).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching user: {str(e)}")
            return None

    def update_user_password(self, user_id: str, new_password_hash: str) -> bool:
        """
        Update user password.
        Args:
            user_id: ID of the user
            new_password_hash: New hashed password
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase.table("users").update({
                "password": new_password_hash
            }).eq("id", user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating password: {str(e)}")
            return False

    def check_username_exists(self, username: str) -> bool:
        """
        Check if username already exists.
        Args:
            username: Username to check
        Returns:
            True if exists, False otherwise
        """
        try:
            response = self.supabase.table("users").select("id").eq("username", username).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking username: {str(e)}")
            return False

    def check_email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        Args:
            email: Email to check
        Returns:
            True if exists, False otherwise
        """
        try:
            response = self.supabase.table("users").select("id").eq("email", email.lower()).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking email: {str(e)}")
            return False

# Test code - commented out to prevent execution on import
# if __name__ == "__main__":
#     SupaBaseClient = SupaBase()
#     print(SupaBaseClient.get_brands())