"""Tests for settings configuration."""
import pytest
from pydantic import ValidationError
from src.settings import Settings, load_settings


class TestSettings:
    """Test settings validation and loading."""
    
    def test_valid_settings(self):
        """Test creation of valid settings."""
        settings = Settings(
            openai_api_key="test_key",
            email_username="test@example.com",
            email_password="test_pass"
        )
        
        assert settings.openai_api_key == "test_key"
        assert settings.request_delay == 2.0  # Default value
        assert "smtp.gmail.com" in settings.user_agents or settings.smtp_server == "smtp.gmail.com"
    
    def test_delay_validation(self):
        """Test request delay validation."""
        with pytest.raises(ValidationError):
            Settings(
                openai_api_key="test",
                email_username="test@example.com",
                email_password="test",
                request_delay=15.0  # Too high
            )
    
    def test_report_size_validation(self):
        """Test report size validation."""
        settings = Settings(
            openai_api_key="test",
            email_username="test@example.com",
            email_password="test",
            max_report_size_mb=100
        )
        
        assert settings.max_report_size_mb == 100
    
    def test_output_dir_creation(self, temp_output_dir):
        """Test that output directory is created."""
        temp_path = str(temp_output_dir / "test_reports")
        
        settings = Settings(
            openai_api_key="test",
            email_username="test@example.com",
            email_password="test",
            output_dir=temp_path
        )
        
        from pathlib import Path
        assert Path(settings.output_dir).exists()