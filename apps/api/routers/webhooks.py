"""
Clerk Webhooks Handler

This module handles webhooks from Clerk to sync users automatically.
"""
from fastapi import APIRouter, Request, Header, HTTPException
import json
import logging
from svix.webhooks import Webhook, WebhookVerificationError

from core.config import get_settings
from services.user_service import UserService
from utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/clerk")
async def handle_clerk_webhook(
    request: Request,
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature"),
):
    """
    Handle webhooks from Clerk.
    
    This endpoint receives webhooks from Clerk and syncs user data with Supabase.
    
    Events handled:
    - user.created: Create user in Supabase
    - user.updated: Update user in Supabase
    - user.deleted: Soft delete user (optional)
    
    Headers:
        svix-id: Unique message ID
        svix-timestamp: Timestamp of when the webhook was sent
        svix-signature: HMAC signature for verification
    
    Returns:
        JSON response with status
    """
    settings = get_settings()
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify webhook signature using Svix
    try:
        wh = Webhook(settings.clerk_webhook_secret)
        payload = wh.verify(body, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature
        })
    except WebhookVerificationError as e:
        logger.warning(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event_type = payload.get("type")
    data = payload.get("data", {})
    
    logger.info(f"Received Clerk webhook: {event_type}")
    
    # Initialize services
    supabase = get_supabase_client()
    user_service = UserService(supabase)
    
    # Handle different event types
    try:
        if event_type == "user.created":
            # Extract user data
            clerk_id = data.get("id")
            email_addresses = data.get("email_addresses", [])
            primary_email_id = data.get("primary_email_address_id")
            
            # Get primary email
            email = None
            if email_addresses:
                primary_email_obj = next(
                    (e for e in email_addresses if e.get("id") == primary_email_id),
                    email_addresses[0] if email_addresses else None
                )
                if primary_email_obj:
                    email = primary_email_obj.get("email_address")
            
            # Default email if none (shouldn't happen with OAuth)
            if not email:
                email = f"{clerk_id}@clerk.placeholder"
                logger.warning(f"No email for user {clerk_id}, using placeholder")
            
            # Create user in Supabase
            user = user_service.get_or_create_user(
                clerk_id=clerk_id,
                email=email,
                username=data.get("username"),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                avatar_url=data.get("image_url"),
            )
            
            logger.info(f"User created in Supabase: {clerk_id} ({email}) - username: {data.get('username')}")
            return {"status": "success", "message": "User created", "user_id": user["id"]}
        
        elif event_type == "user.updated":
            # Extract user data
            clerk_id = data.get("id")
            email_addresses = data.get("email_addresses", [])
            primary_email_id = data.get("primary_email_address_id")
            
            # Get primary email
            email = None
            if email_addresses:
                primary_email_obj = next(
                    (e for e in email_addresses if e.get("id") == primary_email_id),
                    email_addresses[0] if email_addresses else None
                )
                if primary_email_obj:
                    email = primary_email_obj.get("email_address")
            
            # Default email if none
            if not email:
                email = f"{clerk_id}@clerk.placeholder"
            
            # Update user in Supabase
            user = user_service.get_or_create_user(
                clerk_id=clerk_id,
                email=email,
                username=data.get("username"),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                avatar_url=data.get("image_url"),
            )
            
            logger.info(f"User updated in Supabase: {clerk_id} ({email}) - username: {data.get('username')}")
            return {"status": "success", "message": "User updated", "user_id": user["id"]}
        
        elif event_type == "user.deleted":
            # Soft delete: mark user as deleted (optional)
            clerk_id = data.get("id")
            
            # You could implement soft delete here
            # For now, just acknowledge
            logger.info(f"User deleted event received: {clerk_id}")
            return {"status": "success", "message": "User deleted acknowledged"}
        
        else:
            # Unknown event type - just acknowledge
            logger.info(f"Unhandled event type: {event_type}")
            return {"status": "ignored", "message": f"Event type {event_type} not handled"}
            
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}", exc_info=True)
        # Return 200 to avoid Clerk retrying
        return {"status": "error", "message": str(e)}

