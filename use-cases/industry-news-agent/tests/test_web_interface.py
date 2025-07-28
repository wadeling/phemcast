"""Tests for FastAPI web interface."""
import pytest
from fastapi.testclient import TestClient
from src.web_interface import app


class TestWebInterface:
    """Test web interface endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_home_endpoint(self):
        """Test home endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "Industry News Agent" in response.text
    
    def test_status_endpoint(self):
        """Test system status endpoint."""
        response = self.client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_generate_report_invalid_urls(self):
        """Test report generation with no URLs."""
        response = self.client.post(
            "/api/generate-report",
            json={"urls": [], "max_articles": 5}
        )
        assert response.status_code == 422  # Pydantic validation error
    
    def test_form_submission(self):
        """Test form submission."""
        url_data = """https://blog.example.com
https://tech.example.com"""
        
        response = self.client.post(
            "/api/generate-report-form",
            data={
                "urls": url_data,
                "email": "test@example.com",
                "max_articles": "3"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
    
    def test_invalid_email_format(self):
        """Test invalid email format."""
        response = self.client.post(
            "/api/generate-report",
            json={
                "urls": ["https://example.com"],
                "email": "invalid-email",
                "max_articles": 5
            }
        )
        assert response.status_code == 422