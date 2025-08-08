#!/usr/bin/env python3
"""
Test script to verify web scraping functionality with Wiz.io blog.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from settings import load_settings
from web_scraper import AsyncWebScraper
from models import Article


async def test_wiz_scraping():
    """Test scraping Wiz.io blog."""
    print("🧪 Testing Wiz.io blog scraping...")
    
    try:
        # Load settings (minimal for testing)
        settings = load_settings()
        print(f"✅ Settings loaded successfully")
        
        # Test URLs
        test_urls = [
            "https://www.wiz.io/blog",  # Blog index (should extract multiple articles)
            "https://www.wiz.io/blog/celebrating-200-wintegrations-and-the-partners-who-make-it-possible",  # Specific article
        ]
        
        async with AsyncWebScraper(settings) as scraper:
            for i, url in enumerate(test_urls, 1):
                print(f"\n📋 Test {i}: {url}")
                print("-" * 50)
                
                try:
                    articles, errors = await scraper.scrape_blog_articles([url], max_articles=3)
                    
                    if articles:
                        print(f"✅ Successfully scraped {len(articles)} articles:")
                        for j, article in enumerate(articles, 1):
                            print(f"  {j}. {article.title[:80]}...")
                            print(f"     URL: {article.url}")
                            print(f"     Words: {article.word_count}")
                            print(f"     Content preview: {article.content[:100]}...")
                    else:
                        print("❌ No articles found")
                    
                    if errors:
                        print(f"⚠️  Errors encountered:")
                        for error in errors:
                            print(f"    - {error}")
                            
                except Exception as e:
                    print(f"❌ Error scraping {url}: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_wiz_scraping())