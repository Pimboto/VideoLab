"""
User Service

Handles all user-related database operations.
"""
from typing import Optional, Dict, Any
from supabase import Client
from models.user import User, UserCreate, UserUpdate
from core.exceptions import UnauthorizedError


class UserService:
    """Service for user database operations"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def get_user_by_clerk_id(self, clerk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by Clerk ID.

        Args:
            clerk_id: The Clerk user ID

        Returns:
            User dict if found, None otherwise
        """
        try:
            result = self.supabase.table("users") \
                .select("*") \
                .eq("clerk_id", clerk_id) \
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            raise UnauthorizedError(f"Failed to fetch user: {str(e)}")

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by database ID.

        Args:
            user_id: The database user ID (UUID)

        Returns:
            User dict if found, None otherwise
        """
        try:
            result = self.supabase.table("users") \
                .select("*") \
                .eq("id", user_id) \
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            raise UnauthorizedError(f"Failed to fetch user: {str(e)}")

    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        Create a new user in the database.

        Args:
            user_data: UserCreate model with user information

        Returns:
            Created user dict

        Raises:
            UnauthorizedError: If user creation fails
        """
        try:
            result = self.supabase.table("users").insert({
                "clerk_id": user_data.clerk_id,
                "email": user_data.email,
                "username": user_data.username,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "avatar_url": user_data.avatar_url,
            }).execute()

            if not result.data or len(result.data) == 0:
                raise UnauthorizedError("Failed to create user in database")

            return result.data[0]
        except Exception as e:
            raise UnauthorizedError(f"Failed to create user: {str(e)}")

    def update_user(self, user_id: str, user_data: UserUpdate) -> Dict[str, Any]:
        """
        Update user information.

        Args:
            user_id: The database user ID (UUID)
            user_data: UserUpdate model with fields to update

        Returns:
            Updated user dict

        Raises:
            UnauthorizedError: If update fails
        """
        try:
            # Only include fields that are set
            update_data = user_data.model_dump(exclude_unset=True)

            if not update_data:
                # No fields to update
                return self.get_user_by_id(user_id)

            result = self.supabase.table("users") \
                .update(update_data) \
                .eq("id", user_id) \
                .execute()

            if not result.data or len(result.data) == 0:
                raise UnauthorizedError("Failed to update user")

            return result.data[0]
        except Exception as e:
            raise UnauthorizedError(f"Failed to update user: {str(e)}")

    def get_or_create_user(
        self,
        clerk_id: str,
        email: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get existing user or create if doesn't exist.

        This is the main method called during authentication to ensure
        the user exists in our database.

        Args:
            clerk_id: Clerk user ID
            email: User email
            first_name: User first name (optional)
            last_name: User last name (optional)
            avatar_url: User avatar URL (optional)

        Returns:
            User dict (either existing or newly created)

        Raises:
            UnauthorizedError: If operation fails
        """
        # Try to get existing user
        user = self.get_user_by_clerk_id(clerk_id)

        if user:
            # User exists, optionally update their info if changed
            update_needed = False
            update_data = {}

            if email != user.get("email"):
                update_data["email"] = email
                update_needed = True

            if username and username != user.get("username"):
                update_data["username"] = username
                update_needed = True

            if first_name and first_name != user.get("first_name"):
                update_data["first_name"] = first_name
                update_needed = True

            if last_name and last_name != user.get("last_name"):
                update_data["last_name"] = last_name
                update_needed = True

            if avatar_url and avatar_url != user.get("avatar_url"):
                update_data["avatar_url"] = avatar_url
                update_needed = True

            if update_needed:
                user_update = UserUpdate(**update_data)
                user = self.update_user(user["id"], user_update)

            return user

        # User doesn't exist, create new one
        user_data = UserCreate(
            clerk_id=clerk_id,
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
        )

        return self.create_user(user_data)
