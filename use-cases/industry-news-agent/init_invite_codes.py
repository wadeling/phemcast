#!/usr/bin/env python3
"""Initialize invite codes in the database."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import init_db, get_async_db, InviteCode
from src.settings import load_settings
from datetime import datetime, timedelta


async def init_invite_codes():
    """Initialize invite codes in the database."""
    try:
        # Load settings
        settings = load_settings()
        
        # Initialize database
        init_db(settings.database_url)
        
        # Create some invite codes
        invite_codes = [
            "WELCOME2024",
            "INDUSTRY2024", 
            "NEWS2024",
            "AGENT2024",
            "TEST123"
        ]
        
        async with await get_async_db() as session:
            for code in invite_codes:
                # Check if code already exists
                result = await session.execute(
                    f"SELECT code FROM invite_codes WHERE code = '{code}'"
                )
                existing = result.fetchone()
                
                if not existing:
                    # Create new invite code
                    invite_code = InviteCode(
                        code=code,
                        is_used=False,
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=365)  # 1 year expiry
                    )
                    session.add(invite_code)
                    print(f"Created invite code: {code}")
                else:
                    print(f"Invite code {code} already exists")
            
            await session.commit()
            print("Invite codes initialized successfully!")
            
    except Exception as e:
        print(f"Error initializing invite codes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_invite_codes())
