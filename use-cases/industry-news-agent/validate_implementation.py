"""Validation script to test industry news agent implementation."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import settings
import models
import agent


async def validate_implementation():
    """Validate the agent implementation."""
    print("🔍 Validating Industry News Agent Implementation...")
    
    # Test 1: Settings loading
    try:
        print("✅ Testing settings...")
        test_settings = settings.Settings(
            openai_api_key="test_key",
            email_username="test@test.com",
            email_password="test",
            output_dir="test_reports"
        )
        print("   Settings loaded successfully")
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False
    
    # Test 2: Model validation
    try:
        print("✅ Testing models...")
        article = models.Article(
            url="https://test.com",
            title="Test",
            content="Test content",
            company_name="TestCorp"
        )
        print(f"   Article created: {article.title}")
    except Exception as e:
        print(f"❌ Models error: {e}")
        return False
    
    # Test 3: Agent creation
    try:
        print("✅ Testing agent creation...")
        agent_instance = agent.create_agent(test_settings)
        print("   Agent created successfully")
    except Exception as e:
        print(f"❌ Agent error: {e}")
        return False
    
    print("\n🎉 All core components validated successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(validate_implementation())
    sys.exit(0 if success else 1)