"""Tests for Pydantic models."""
import pytest
from src.models import Article, CompanyInsights, ReportRequest
from datetime import datetime


class TestModels:
    """Test model validation and methods."""
    
    def test_article_creation(self):
        """Test Article model creation and validation."""
        article = Article(
            url="https://example.com/article",
            title="Test Title",
            content="Test content here",
            company_name="TestCorp"
        )
        
        assert article.url == "https://example.com/article"
        assert article.title == "Test Title"
        assert article.content == "Test content here"
        assert article.company_name == "TestCorp"
        assert article.word_count == 0  # Default value
    
    def test_article_url_validation(self):
        """Test URL validation in Article."""
        with pytest.raises(ValueError):
            Article(
                url="invalid-url",
                title="Test",
                content="Test",
                company_name="Test"
            )
    
    def test_company_insights_validation(self):
        """Test CompanyInsights validation."""
        insights = CompanyInsights(
            company_name="TestCorp",
            article_count=5,
            key_insights=["Insight 1", "Insight 2"],
            trend_score=0.8
        )
        
        assert insights.company_name == "TestCorp"
        assert insights.trend_score == 0.8
    
    def test_company_insights_trend_score_bounds(self):
        """Test trend score stays within bounds."""
        with pytest.raises(ValueError):
            CompanyInsights(
                company_name="Test",
                article_count=1,
                trend_score=1.5  # Should be <= 1.0
            )
    
    def test_article_word_count_calculation(self):
        """Test article word count calculation."""
        article = Article(
            url="https://example.com/test",
            title="Test",
            content="This is a test article with several words in it",
            company_name="TestCorp"
        )
        
        assert article.calculate_word_count() == 10
    
    def test_report_request_parsing(self):
        """Test ReportRequest URL parsing."""
        request = ReportRequest(
            urls="https://example1.com\nhttps://example2.com\n",
            email="test@example.com",
            max_articles=3
        )
        
        assert len(request.urls) == 2
        assert request.urls[0] == "https://example1.com"
        assert request.max_articles == 3