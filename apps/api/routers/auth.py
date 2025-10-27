"""
Authentication test routes

These routes are for testing authentication and getting user information.
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from core.dependencies import get_current_user, get_optional_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current authenticated user information.

    **Requires authentication.**

    Returns user information from the database including:
    - UUID (id)
    - Clerk ID
    - Email
    - Name
    - Avatar
    - Timestamps

    ### Example Response:
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "clerk_id": "user_2abc123xyz",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "avatar_url": "https://...",
        "created_at": "2025-01-27T12:00:00"
    }
    ```

    ### Errors:
    - **401 Unauthorized**: No token provided or invalid token
    - **401 Unauthorized**: Token expired
    - **401 Unauthorized**: User not found in database
    """
    return {
        "id": current_user["id"],
        "clerk_id": current_user["clerk_id"],
        "email": current_user["email"],
        "first_name": current_user.get("first_name"),
        "last_name": current_user.get("last_name"),
        "avatar_url": current_user.get("avatar_url"),
        "created_at": str(current_user["created_at"]),
        "updated_at": str(current_user["updated_at"]),
    }


@router.get("/test-public")
async def test_public() -> Dict[str, str]:
    """
    Public endpoint - no authentication required.

    Anyone can access this endpoint without providing a token.
    Useful for testing that the API is running.

    ### Example Response:
    ```json
    {
        "message": "This is a public endpoint",
        "requires_auth": false
    }
    ```
    """
    return {
        "message": "This is a public endpoint",
        "requires_auth": False,
    }


@router.get("/test-optional")
async def test_optional_auth(
    current_user: Dict[str, Any] | None = Depends(get_optional_user)
) -> Dict[str, Any]:
    """
    Optional authentication endpoint.

    Returns different responses for authenticated vs unauthenticated users.
    This pattern is useful for endpoints that provide enhanced features
    for authenticated users but still work for guests.

    ### Authenticated Response:
    ```json
    {
        "authenticated": true,
        "message": "Hello user@example.com!",
        "user_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    ### Unauthenticated Response:
    ```json
    {
        "authenticated": false,
        "message": "Hello guest! Sign in for personalized experience."
    }
    ```
    """
    if current_user:
        return {
            "authenticated": True,
            "message": f"Hello {current_user['email']}!",
            "user_id": current_user["id"],
            "user_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip() or "User",
        }
    else:
        return {
            "authenticated": False,
            "message": "Hello guest! Sign in for personalized experience.",
        }


@router.get("/status")
async def auth_status(
    current_user: Dict[str, Any] | None = Depends(get_optional_user)
) -> Dict[str, Any]:
    """
    Check authentication status without requiring auth.

    Returns whether the current request is authenticated or not,
    along with basic information if authenticated.

    ### Response:
    ```json
    {
        "authenticated": true,
        "user": {
            "id": "...",
            "email": "..."
        }
    }
    ```
    """
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user["id"],
                "email": current_user["email"],
                "clerk_id": current_user["clerk_id"],
            },
        }
    else:
        return {
            "authenticated": False,
            "user": None,
        }
