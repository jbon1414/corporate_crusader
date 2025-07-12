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

    def get_brands(self) -> List[Dict]:
        """
        Fetch all brands from the Supabase database.
        Returns:
            List of brand dictionaries
        """
        try:
            response = self.supabase.table("brands").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error fetching brands: {str(e)}")
            return []

    def get_brand_by_id(self, brand_id: str) -> Optional[Dict]:
        """
        Fetch a specific brand by ID.
        Args:
            brand_id: UUID string of the brand
        Returns:
            Brand dictionary or None if not found
        """
        try:
            response = self.supabase.table("brands").select("*").eq("id", brand_id).execute()
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

    def delete_brand(self, brand_id: str) -> bool:
        """
        Delete a brand from the database.
        Args:
            brand_id: UUID string of the brand to delete
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase.table("brands").delete().eq("id", brand_id).execute()
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

    def get_posts_by_brand(self, brand_id: str) -> List[Dict]:
        """
        Fetch all posts for a specific brand from the 'posts' table.
        Args:
            brand_id: UUID string of the brand
        Returns:
            List of post dictionaries
        """
        try:
            response = self.supabase.table("posts").select("*").eq("brand_id", brand_id).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching posts for brand {brand_id}: {str(e)}")
            return []

#test 
SupaBaseClient = SupaBase()
print(SupaBaseClient.get_brands())
