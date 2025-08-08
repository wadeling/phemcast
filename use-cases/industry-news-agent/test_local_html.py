#!/usr/bin/env python3
"""
Test script using local HTML file to verify scraping logic.
"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_local_html():
    """Test scraping logic using local HTML file."""
    print("🧪 Testing with local Wiz.io HTML file...")
    
    try:
        # Read local HTML file
        html_file = Path(__file__).parent / "data" / "wize-io-blog.html"
        if not html_file.exists():
            print(f"❌ HTML file not found: {html_file}")
            return
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"✅ HTML file loaded: {len(html_content)} characters")
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        print(f"✅ HTML parsed successfully")
        
        # Test link extraction
        base_url = "https://www.wiz.io/blog"
        
        # Create a minimal scraper instance just for testing
        class TestScraper:
            def _find_article_links(self, soup, base_url):
                """Test link extraction."""
                links = []
                
                # Enhanced selectors for modern blogs including Wiz.io
                selectors = [
                    'a[href^="/blog/"]',
                    'article a[href^="/blog/"]',
                    'section a[href^="/blog/"]',
                    'h2 a[href^="/blog/"]',
                    'h3 a[href^="/blog/"]',
                    'a[href*="/blog/"]',
                ]
                
                for selector in selectors:
                    found = soup.select(selector)
                    print(f"🔍 Selector '{selector}' found {len(found)} links")
                    
                    for link in found:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(base_url, href)
                            if self._is_valid_article_url(full_url, base_url):
                                links.append(link)
                                if len(links) >= 10:  # Limit for testing
                                    break
                    if links:
                        break
                
                return links
            
            def _is_valid_article_url(self, full_url, base_url):
                """Test URL validation."""
                from urllib.parse import urlparse
                
                parsed = urlparse(full_url)
                base_parsed = urlparse(base_url)
                
                # Check if same domain
                if parsed.netloc != base_parsed.netloc:
                    return False
                
                # Check if it's a blog article URL
                path = parsed.path.lower()
                
                # Valid blog article patterns
                valid_patterns = [
                    '/blog/',
                    '/articles/',
                    '/news/',
                    '/post/',
                    '/story/'
                ]
                
                # Avoid non-article pages
                invalid_patterns = [
                    '/blog/tag/',
                    '/blog/category/',
                    '/blog/author/',
                    '/blog/page/',
                    '/blog/archive/',
                    '/tag/',
                    '/category/',
                    '/author/',
                    '/page/',
                    '/archive/',
                    '/search',
                    '/feed',
                    '/rss'
                ]
                
                is_valid = any(pattern in path for pattern in valid_patterns)
                is_invalid = any(pattern in path for pattern in invalid_patterns)
                
                return is_valid and not is_invalid and len(path) > len('/blog/')
        
        test_scraper = TestScraper()
        article_links = test_scraper._find_article_links(soup, base_url)
        
        print(f"\n📋 Found {len(article_links)} article links:")
        for i, link in enumerate(article_links, 1):
            href = link.get('href')
            full_url = urljoin(base_url, href)
            title_text = link.get_text(strip=True)[:60]
            print(f"  {i}. {title_text}... -> {full_url}")
        
        # Test specific article detection
        test_urls = [
            "https://www.wiz.io/blog/celebrating-200-wintegrations-and-the-partners-who-make-it-possible",
            "https://www.wiz.io/blog/critical-vulnerability-base44",
            "https://www.wiz.io/blog",  # Should be detected as blog index
            "https://www.wiz.io/blog/tag/ai",  # Should be excluded
        ]
        
        print(f"\n🔍 Testing specific article URL detection:")
        for url in test_urls:
            is_specific = test_scraper._is_valid_article_url(url, "https://www.wiz.io")
            print(f"  {url} -> {'✅ Specific article' if is_specific else '❌ Not specific article'}")
        
        print(f"\n🎉 Local HTML test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_local_html()