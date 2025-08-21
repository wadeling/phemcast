"""WeChat authentication service for QR code login."""
import asyncio
import uuid
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
import qrcode
import base64
from io import BytesIO

try:
    from .models import User, WeChatLoginState, LoginResponse
    from .settings import get_settings
    from .logging_config import get_logger
except ImportError:
    from models import User, WeChatLoginState, LoginResponse
    from settings import get_settings
    from logging_config import get_logger

logger = get_logger(__name__)


class WeChatAuthService:
    """WeChat authentication service for handling QR code login."""
    
    def __init__(self):
        self.settings = get_settings()
        self.login_states: Dict[str, WeChatLoginState] = {}
        self.users: Dict[str, User] = {}  # In production, use database
        self._cleanup_task = None
        
        # Start cleanup task only if we're in an event loop
        try:
            loop = asyncio.get_running_loop()
            if not self._cleanup_task:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_states())
        except RuntimeError:
            # No event loop running, skip cleanup task for now
            pass
    
    async def generate_qr_code(self) -> WeChatLoginState:
        """Generate a new QR code for WeChat login."""
        try:
            # Generate unique state ID
            state_id = str(uuid.uuid4())
            
            # Create QR code content (in production, this would be a WeChat URL)
            qr_content = f"https://open.weixin.qq.com/connect/qrconnect?appid={self.settings.wechat_app_id}&redirect_uri={self.settings.host}:{self.settings.port}/api/wechat/callback&response_type=code&scope=snsapi_login&state={state_id}#wechat_redirect"
            
            # Generate QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            qr_code_url = f"data:image/png;base64,{qr_code_base64}"
            
            # Create login state
            expires_at = datetime.now() + timedelta(seconds=self.settings.qr_code_expire_seconds)
            login_state = WeChatLoginState(
                state_id=state_id,
                qr_code_url=qr_code_url,
                expires_at=expires_at
            )
            
            # Store state
            self.login_states[state_id] = login_state
            
            logger.info(f"Generated QR code for state: {state_id}")
            return login_state
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {str(e)}")
            raise
    
    async def check_login_status(self, state_id: str) -> Optional[User]:
        """Check if user has completed login for given state."""
        if state_id not in self.login_states:
            return None
        
        state = self.login_states[state_id]
        
        # Check if expired
        if datetime.now() > state.expires_at:
            del self.login_states[state_id]
            return None
        
        # Check if used
        if state.is_used and state.user_id:
            return self.users.get(str(state.user_id))
        
        return None
    
    async def handle_wechat_callback(self, code: str, state: str) -> LoginResponse:
        """Handle WeChat callback after user scans QR code."""
        try:
            if state not in self.login_states:
                return LoginResponse(
                    success=False,
                    message="Invalid or expired login state"
                )
            
            state_obj = self.login_states[state]
            
            # Check if expired
            if datetime.now() > state_obj.expires_at:
                del self.login_states[state]
                return LoginResponse(
                    success=False,
                    message="Login state expired"
                )
            
            # Check if already used
            if state_obj.is_used:
                return LoginResponse(
                    success=False,
                    message="Login state already used"
                )
            
            # In production, exchange code for access token and user info
            # For demo purposes, we'll simulate the process
            await asyncio.sleep(1)  # Simulate API call
            
            # Generate user info (in production, get from WeChat API)
            wechat_openid = f"wx_{uuid.uuid4().hex[:16]}"
            wechat_nickname = f"User_{uuid.uuid4().hex[:8]}"
            
            # Check if user exists
            existing_user = None
            for user in self.users.values():
                if user.wechat_openid == wechat_openid:
                    existing_user = user
                    break
            
            if existing_user:
                # Update last login
                existing_user.last_login = datetime.now()
                user = existing_user
            else:
                # Create new user with generated username
                username = self._generate_username()
                user = User(
                    username=username,
                    wechat_openid=wechat_openid,
                    wechat_nickname=wechat_nickname
                )
                self.users[str(user.id)] = user
            
            # Mark state as used
            state_obj.is_used = True
            state_obj.user_id = user.id
            
            logger.info(f"User {user.username} logged in via WeChat")
            
            return LoginResponse(
                success=True,
                message="Login successful",
                user=user,
                redirect_url="/dashboard"
            )
            
        except Exception as e:
            logger.error(f"Failed to handle WeChat callback: {str(e)}")
            return LoginResponse(
                success=False,
                message=f"Login failed: {str(e)}"
            )
    
    def _generate_username(self) -> str:
        """Generate a unique username for new users."""
        import random
        import string
        
        # Generate username with format: User_XXXX
        while True:
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            username = f"User_{suffix}"
            
            # Check if username exists
            if not any(user.username == username for user in self.users.values()):
                return username
    
    async def _cleanup_expired_states(self):
        """Clean up expired login states periodically."""
        while True:
            try:
                current_time = datetime.now()
                expired_states = [
                    state_id for state_id, state in self.login_states.items()
                    if current_time > state.expires_at
                ]
                
                for state_id in expired_states:
                    del self.login_states[state_id]
                
                if expired_states:
                    logger.info(f"Cleaned up {len(expired_states)} expired login states")
                
                # Wait 1 minute before next cleanup
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(60)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_user_by_openid(self, openid: str) -> Optional[User]:
        """Get user by WeChat OpenID."""
        for user in self.users.values():
            if user.wechat_openid == openid:
                return user
        return None


# Global instance
wechat_auth_service = WeChatAuthService()
