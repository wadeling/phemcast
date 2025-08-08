#!/usr/bin/env python3
"""
Test script to verify the AIContentAnalysisTool fixes work correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import Article
from src.settings import load_settings
from src.tools import AIContentAnalysisTool


def test_tool_input_handling():
    """Test that the AIContentAnalysisTool handles various input formats correctly."""
    print("🧪 Testing AIContentAnalysisTool input handling...")
    
    try:
        # Load minimal settings for testing
        settings = load_settings()
        print("✅ Settings loaded")
        
        # Create test articles
        test_articles = [
            Article(
                url="https://example.com/article1",
                title="Test Article 1",
                content="This is a test article about AI and machine learning.",
                company_name="TestCompany",
                word_count=50
            ),
            Article(
                url="https://example.com/article2", 
                title="Test Article 2",
                content="Another test article about cloud security and best practices.",
                company_name="TestCompany",
                word_count=45
            )
        ]
        print(f"✅ Created {len(test_articles)} test articles")
        
        # Create analyzer
        analyzer = AIContentAnalysisTool(settings)
        print("✅ AIContentAnalysisTool created")
        
        # Test different input formats
        test_cases = [
            ("List of articles (positional)", [test_articles], {}),
            ("Single article (positional)", [test_articles[0]], {}),
            ("List with config (positional)", [test_articles, {}], {}),
            ("List of articles (keyword)", [], {"articles": test_articles}),
            ("Single article (keyword)", [], {"articles": test_articles[0]}),
        ]
        
        for test_name, args, kwargs in test_cases:
            print(f"\n🔍 Testing: {test_name}")
            try:
                result = analyzer._run(*args, **kwargs)
                if isinstance(result, list) and len(result) > 0:
                    print(f"  ✅ Success: Returned {len(result)} articles")
                    # Check if articles have analysis added
                    if hasattr(result[0], 'summary') or hasattr(result[0], 'key_insights'):
                        print(f"  ✅ Analysis fields present")
                    else:
                        print(f"  ⚠️  Analysis fields missing (expected in real run)")
                else:
                    print(f"  ❌ Unexpected result: {result}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print(f"\n🎉 Tool input handling test completed!")
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()


def test_real_workflow_simulation():
    """Simulate the real workflow to ensure everything works end-to-end."""
    print(f"\n🔄 Testing real workflow simulation...")
    
    try:
        settings = load_settings()
        analyzer = AIContentAnalysisTool(settings)
        
        # Simulate the actual call from agent.py
        test_articles = [
            Article(
                url="https://blog.wiz.io/test-article",
                title="Cloud Security Trends 2025",
                content="Cloud security continues to evolve with new threats and technologies.",
                company_name="Wiz",
                word_count=30
            )
        ]
        
        # This is how it's called in agent.py line 207
        print("📝 Simulating analyzer._run(articles) call from agent.py...")
        try:
            result = analyzer._run(articles=test_articles)
            print(f"✅ Direct _run successful: {type(result)} with {len(result) if isinstance(result, list) else 'N/A'} items")
        except Exception as e:
            print(f"❌ Direct _run failed: {e}")
        
        print(f"\n🎉 Real workflow simulation completed!")
        
    except Exception as e:
        print(f"❌ Workflow simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_tool_input_handling()
    test_real_workflow_simulation()