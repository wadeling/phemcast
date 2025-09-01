"""Session management for user authentication."""
import uuid
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt

from models import User
from settings import get_settings
from logging_config import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages user sessions and JWT tokens."""
    
    def __init__(self):
        self.settings = get_settings()
        self.active_sessions: Dict[str, Dict] = {}  # In production, use Redis
    
    def create_session(self, user: User) -> str:
        """Create a new session for a user."""
        try:
            # Generate session token
            session_id = str(uuid.uuid4())
            
            # Create JWT token
            payload = {
                "sub": str(user.id),
                "username": user.username,
                "openid": user.wechat_openid,
                "exp": datetime.utcnow() + timedelta(minutes=self.settings.session_expire_minutes),
                "iat": datetime.utcnow(),
                "session_id": session_id
            }
            
            token = jwt.encode(payload, self.settings.secret_key, algorithm="HS256")
            
            # Store session info
            session_data = {
                "user_id": str(user.id),
                "username": user.username,
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=self.settings.session_expire_minutes)
            }
            
            self.active_sessions[session_id] = session_data
            
            logger.info(f"Created session for user {user.username}: {session_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and return payload if valid."""
        try:
            payload = jwt.decode(token, self.settings.secret_key, algorithms=["HS256"])
            
            # Check if session exists and is active
            session_id = payload.get("session_id")
            if not session_id or session_id not in self.active_sessions:
                logger.warning(f"Session not found: {session_id}")
                return None
            
            session_data = self.active_sessions[session_id]
            
            # Check if session expired
            if datetime.now() > session_data["expires_at"]:
                del self.active_sessions[session_id]
                logger.info(f"Session expired: {session_id}")
                return None
            
            # Update last activity
            session_data["last_activity"] = datetime.now()
            
            return payload
            
        except JWTError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[Dict]:
        """Get user information from token."""
        payload = self.validate_token(token)
        if payload:
            return {
                "user_id": payload["sub"],
                "username": payload["username"],
                "openid": payload["openid"]
            }
        return None
    
    def revoke_session(self, token: str) -> bool:
        """Revoke a user session."""
        try:
            payload = jwt.decode(token, self.settings.secret_key, algorithms=["HS256"])
            session_id = payload.get("session_id")
            
            if session_id and session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Session revoked: {session_id}")
                return True
            
            return False
            
        except JWTError:
            return False
        except Exception as e:
            logger.error(f"Error revoking session: {str(e)}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session_data in self.active_sessions.items()
            if current_time > session_data["expires_at"]
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        return len(self.active_sessions)


# Global instance
session_manager = SessionManager()
