"""Pytest configuration for industry news agent tests."""
import pytest
from unittest.mock import Mock
from pathlib import Path
import tempfile
import os

from src.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return Settings(
        openai_api_key="test_key",
        email_username="test@example.com",
        email_password="test_password",
        output_dir="test_reports",
        request_delay=0.1  # Fast for tests
    )


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_articles():
    """Sample articles for testing."""
    from src.models import Article
    from datetime import datetime
    
    return [
        Article(
            url="https://example.com/article1",
            title="Test Article 1",
            content="This is a test article about AI innovations.",
            company_name="TestCorp",
            author="John Doe",
            key_insights=["AI is advancing rapidly", "New models are more efficient"],
            word_count=150
        ),
        Article(
            url="https://example.com/article2",
            title="Test Article 2",
            content="Another test article about cloud computing trends.",
            company_name="TechCorp",
            author="Jane Smith",
            key_insights=["Cloud adoption increasing", "Security improvements noted"],
            word_count=200
        )
    ]