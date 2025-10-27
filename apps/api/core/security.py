"""
Security utilities for JWT verification and authentication

This module handles Clerk JWT token verification and user authentication.
"""
import jwt
import requests
from functools import lru_cache
from typing import Dict, Any
from core.config import get_settings
from core.exceptions import UnauthorizedError


@lru_cache(maxsize=1)
def get_clerk_jwks() -> Dict[str, Any]:
    """
    Fetch Clerk's JSON Web Key Set (JWKS) for JWT verification.

    This is cached to avoid hitting the Clerk API on every request.
    The cache is invalidated when the server restarts.

    Returns:
        Dict containing the JWKS keys

    Raises:
        UnauthorizedError: If fetching JWKS fails
    """
    settings = get_settings()

    try:
        response = requests.get(settings.clerk_jwks_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise UnauthorizedError(
            f"Failed to fetch Clerk JWKS: {str(e)}",
            {"url": settings.clerk_jwks_url}
        )


def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Verify a Clerk JWT token and return its payload.

    Args:
        token: The JWT token to verify

    Returns:
        Dict containing the token payload with user information:
        - sub: Clerk user ID
        - email: User email
        - first_name: User first name (optional)
        - last_name: User last name (optional)

    Raises:
        UnauthorizedError: If token is invalid, expired, or verification fails
    """
    try:
        # Decode the token header to get the key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise UnauthorizedError("Token missing 'kid' in header")

        # Get JWKS and find the matching key
        jwks = get_clerk_jwks()
        keys = jwks.get("keys", [])

        # Find the key that matches the kid from the token
        key = next((k for k in keys if k.get("kid") == kid), None)

        if not key:
            raise UnauthorizedError(
                f"No matching key found for kid: {kid}",
                {"kid": kid, "available_keys": len(keys)}
            )

        # Convert JWK to PEM format for verification
        try:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        except Exception as e:
            raise UnauthorizedError(
                f"Failed to convert JWK to public key: {str(e)}",
                {"kid": kid}
            )

        # Verify and decode the token
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={
                    "verify_aud": False,  # Clerk doesn't use audience claim
                    "verify_signature": True,
                    "verify_exp": True,
                    "require_exp": True,
                }
            )
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise UnauthorizedError(f"Invalid token: {str(e)}")

        return payload

    except UnauthorizedError:
        # Re-raise UnauthorizedError as-is
        raise
    except Exception as e:
        # Catch any other unexpected errors
        raise UnauthorizedError(
            f"Token verification failed: {str(e)}",
            {"error_type": type(e).__name__}
        )


def extract_user_info(token_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from a verified Clerk JWT payload.

    Args:
        token_payload: The verified JWT payload

    Returns:
        Dict containing user information:
        - clerk_id: Clerk user ID
        - email: User email
        - first_name: User first name (if available)
        - last_name: User last name (if available)
    """
    return {
        "clerk_id": token_payload.get("sub"),
        "email": token_payload.get("email", ""),
        "first_name": token_payload.get("first_name"),
        "last_name": token_payload.get("last_name"),
    }
