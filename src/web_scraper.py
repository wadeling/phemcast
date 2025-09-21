"""Async web scraping with rate limiting and error handling."""
import asyncio
import aiohttp
import feedparser
import re
import json
import subprocess
import tempfile
import os
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import random
import traceback
from datetime import datetime
import hashlib
import logging
from models import Article
from settings import Settings
from crawl4ai import AsyncWebCrawler

logger = logging.getLogger(__name__)
class WebScrapingError(Exception):
    """Custom exception for web scraping errors."""
    pass


class AsyncWebScraper:
    """Async web scraper with rate limiting and platform detection."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Dict] = {}
        
    async def __aenter__(self):
        """Context manager entry."""
        timeout = aiohttp.ClientTimeout(total=self.settings.timeout)
        connector = aiohttp.TCPConnector(
            limit=self.settings.max_concurrent_requests,
            limit_per_host=2  # Be respectful to individual hosts
        )
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={"User-Agent": random.choice(self.settings.user_agents)}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.close()
    
    async def scrape_blog_articles(
        self, urls: List[str], max_articles: int = 5, pre_fetched_articles: List[Dict] = None
    ) -> Tuple[List[Article], List[str]]:
        """
        Scrape articles from multiple blog URLs with rate limiting and deduplication.
        
        Args:
            urls: List of blog URLs to scrape
            max_articles: Maximum articles per blog
            
        Returns:
            Tuple of (articles, error_messages)
        """
        all_articles = []
        errors = []
        seen_urls = set()
        
        # If we have pre-fetched articles, use them first
        if pre_fetched_articles:
            logger.info(f"Using {len(pre_fetched_articles)} pre-fetched articles")
            for article_data in pre_fetched_articles:
                if article_data.get("url") and article_data["url"] not in seen_urls:
                    article = Article(
                        title=article_data.get("title", ""),
                        url=article_data.get("url", ""),
                        published=article_data.get("published", ""),
                        summary=article_data.get("summary", ""),
                        content=article_data.get("content", "")
                    )
                    seen_urls.add(article.url)
                    all_articles.append(article)
        
        # Process URLs with delay between requests (only if we need more articles)
        if len(all_articles) < max_articles * len(urls):
            for i, url in enumerate(urls):
                if i > 0:
                    await asyncio.sleep(self.settings.request_delay)
            
                try:
                    url_articles = await self._scrape_single_blog(url, max_articles)
                    
                    # Deduplicate articles from this URL
                    unique_articles = []
                    for article in url_articles:
                        if article.url not in seen_urls:
                            seen_urls.add(article.url)
                            unique_articles.append(article)
                            if len(unique_articles) >= max_articles:
                                break  # Stop when we have enough unique articles
                    
                    all_articles.extend(unique_articles)
                    
                    if len(unique_articles) < len(url_articles):
                        print(f"⚠️  Removed {len(url_articles) - len(unique_articles)} duplicate articles from {url}")
                    
                except Exception as e:
                    errors.append(f"Error scraping {url}: {str(e)}")
        
        # Final deduplication across all URLs
        final_articles = []
        final_seen_urls = set()
        
        for article in all_articles:
            if article.url not in final_seen_urls:
                final_seen_urls.add(article.url)
                final_articles.append(article)
        
        if len(final_articles) < len(all_articles):
            print(f"⚠️  Removed {len(all_articles) - len(final_articles)} cross-URL duplicate articles")
        
        return final_articles, errors
    
    async def _scrape_single_blog(
        self, url: str, max_articles: int
    ) -> List[Article]:
        """Scrape a single blog/website."""
        try:
            # Normalize URL first
            url = self._normalize_url(url)
            
            # Check if URL is already a specific article
            if self._is_specific_article_url(url):
                # Scrape this single article directly
                article_data = await self._scrape_single_article(url)
                if article_data:
                    company_name = self._extract_company_name(url)
                    article = Article(
                        url=article_data['url'],
                        title=article_data['title'],
                        content=article_data['content'],
                        company_name=company_name,
                        author=article_data.get('author'),
                        publish_date=article_data.get('publish_date'),
                        word_count=len(article_data['content'].split())
                    )
                    return [article]
                else:
                    return []
            
            # Otherwise, treat as blog index page with multiple articles
            if self._is_rss_feed(url):
                return await self._scrape_rss(url, max_articles)
            elif "aquasec.com" in url.lower():
                # Try Scira.ai API first, then fallback to curl
                if self.settings.enable_scira_api and self.settings.scira_api_key:
                    try:
                        return await self._scrape_with_scira_api(url, max_articles)
                    except Exception as e:
                        logger.warning(f"Scira.ai API failed, falling back to curl: {e}")
                
                # Fallback to curl method
                return await self._scrape_with_curl(url, max_articles)
            elif "medium.com" in url.lower():
                return await self._scrape_medium(url, max_articles)
            elif "wordpress.com" in url or "/wp-content/" in url.lower():
                return await self._scrape_wordpress(url, max_articles)
            else:
                return await self._scrape_generic_blog(url, max_articles)
                
        except Exception as e:
            raise WebScrapingError(f"Failed to scrape {url}: {str(e)}")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize and validate URL format."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url.rstrip("/")
    
    def _is_rss_feed(self, url: str) -> bool:
        """Check if URL is an RSS feed."""
        rss_indicators = ["/feed", "/rss", ".xml", "/atom"]
        return any(indicator in url.lower() for indicator in rss_indicators)
    
    async def _scrape_rss(self, url: str, max_articles: int) -> List[Article]:
        """Scrape articles from RSS feed."""
        try:
            # For RSS, we use feedparser which is synchronous
            feed = feedparser.parse(url)
            
            if not feed.entries:
                return []
            
            articles = []
            for entry in feed.entries[:max_articles * 2]:  # Get more entries to account for duplicates
                # Get content from entry
                content = (entry.get("description", "") or 
                          entry.get("summary", "") or 
                          entry.get("content", ""))
                
                # Parse date
                publish_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    publish_date = datetime(*entry.published_parsed[:6])
                
                # Extract company name from domain
                company_name = self._extract_company_name(url)
                
                article = Article(
                    url=entry.link,
                    title=entry.title,
                    content=content,
                    company_name=company_name,
                    author=getattr(entry, "author", None),
                    publish_date=publish_date,
                    word_count=len(content.split())
                )
                articles.append(article)
            
            return articles
            
        except Exception as e:
            raise WebScrapingError(f"RSS scraping failed: {str(e)}")
    
    async def _scrape_medium(self, url: str, max_articles: int) -> List[Article]:
        """Scrape Medium blog posts."""
        if ".com/@" not in url.lower():
            url = f"{url}/latest"
        
        return await self._scrape_generic_blog(url, max_articles)
    
    async def _scrape_wordpress(self, url: str, max_articles: int) -> List[Article]:
        """Scrape WordPress blog."""
        wp_url = url + "/wp-json/wp/v2/posts"
        articles = []
        
        try:
            async with self.session.get(wp_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    company_name = self._extract_company_name(url)
                    
                    for post in data[:max_articles]:
                        content = self._extract_text_from_html(
                            post.get("content", {}).get("rendered", "")
                        )
                        
                        article = Article(
                            url=post["link"],
                            title=post["title"]["rendered"],
                            content=content,
                            company_name=company_name,
                            publish_date=datetime.fromisoformat(post["date"]),
                            word_count=len(content.split())
                        )
                        articles.append(article)
        except Exception:
            # Fallback to generic scraping
            articles = await self._scrape_generic_blog(url, max_articles)
        
        return articles
    
    async def _scrape_generic_blog(self, url: str, max_articles: int) -> List[Article]:
        """Scrape generic blog using unified fetching logic."""
        try:
            # Use unified page content fetching
            html_content = await self._fetch_page_content(url)
            if not html_content:
                logger.warning(f"Failed to fetch content from {url}, returning empty list")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            company_name = self._extract_company_name(url)
            
            # Use unified article extraction logic
            articles = await self._extract_articles_from_html(soup, url, max_articles, company_name, scrape_full_content=True)
            
            return articles
                
        except Exception as e:
            logger.error(f"Generic blog scraping failed for {url}: {e}")
            return []
    
    def _extract_company_name(self, url: str) -> str:
        """Extract company name from URL domain."""
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        parts = domain.split(".")
        if len(parts) >= 2:
            return parts[-2].capitalize()
        return domain
    
    def _find_article_links(self, soup: BeautifulSoup, base_url: str) -> List:
        """Find article links in the page."""
        links = []
        
        # Enhanced selectors for modern blogs including Wiz.io
        selectors = [
            # Modern blog frameworks (Next.js, React, etc.)
            'a[href^="/blog/"]',
            'article a[href^="/blog/"]',
            'section a[href^="/blog/"]',
            
            # Traditional blog selectors
            'h2 a[href^="/blog/"]',
            'h3 a[href^="/blog/"]',
            '.post-title a[href^="/blog/"]',
            '.entry-title a[href^="/blog/"]',
            
            # Generic article links
            'a[href*="/blog/"]',
            '.blog-post a[href*="/blog/"]',
            
            # Fallback selectors
            'h2 a',
            'h3 a',
            '.post-title a',
            '.entry-title a',
            'article a',
            '.blog-title a'
        ]
        
        for selector in selectors:
            found = soup.select(selector)
            for link in found:
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute
                    full_url = urljoin(base_url, href)
                    
                    # Filter for blog articles and avoid navigation/other pages
                    if self._is_valid_article_url(full_url, base_url):
                        if full_url not in links:  
                            links.append(full_url)
                        if len(links) >= 50:  # Increased limit to support deduplication
                            break
            if links:
                break
        
        return links
    
    def _is_specific_article_url(self, url: str) -> bool:
        """Check if URL is a specific article URL (not a blog index)."""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check if it looks like a specific article
        # These patterns indicate specific articles rather than blog indexes
        specific_article_patterns = [
            '/blog/',  # Has blog path
            '/articles/',
            '/news/',
            '/post/',
            '/story/'
        ]
        
        # Must match a specific pattern and NOT be a blog index or listing
        is_specific = any(pattern in path for pattern in specific_article_patterns)
        
        # Exclude blog indexes and listings
        exclusion_patterns = [
            '/blog$',  # Ends with /blog (the index)
            '/blog/$',  # Ends with /blog/
            '/blog/page/',
            '/blog/category/',
            '/blog/tag/',
            '/blog/author/',
            '/blog/archive/',
            '/tag/',
            '/category/',
            '/page/',
            '/archive/',
            '/feed',
            '/rss'
        ]
        
        is_excluded = any(pattern in path for pattern in exclusion_patterns)
        
        # Also check if path has more than just the base blog path
        # e.g., "/blog/article-title" is specific, "/blog" is not
        path_parts = path.strip('/').split('/')
        is_specific_length = len(path_parts) >= 2  # At least blog/article-name
        
        return is_specific and not is_excluded and is_specific_length
    
    def _is_valid_article_url(self, full_url: str, base_url: str) -> bool:
        """Check if URL is a valid article URL."""
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
            '/blog/',  # Main blog articles
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
        
        # Check if matches valid patterns
        is_valid = any(pattern in path for pattern in valid_patterns)
        
        # Check if doesn't match invalid patterns
        is_invalid = any(pattern in path for pattern in invalid_patterns)
        
        # Must be valid and not invalid
        # Also ensure it's not just "/blog/" (the blog index)
        return is_valid and not is_invalid and len(path) > len('/blog/')
    
    def _find_largest_text_block(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the largest text block in the page as fallback content."""
        text_blocks = []
        
        # Common content-bearing elements
        content_elements = soup.find_all(['div', 'section', 'main', 'article'], recursive=True)
        
        for element in content_elements:
            text = element.get_text(strip=True)
            if len(text) > 200:  # Minimum reasonable content length
                text_blocks.append((element, len(text)))
        
        if text_blocks:
            # Sort by text length and return the largest
            text_blocks.sort(key=lambda x: x[1], reverse=True)
            return text_blocks[0][0]
        
        return None
    
    async def _fetch_page_content(self, url: str, min_content_length: int = 100) -> Optional[str]:
        """Unified page content fetching with session.get fallback to curl."""
        try:
            # First try: Use session.get
            logger.debug(f"Attempting to fetch {url} with session.get")
            async with self.session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    if html_content and len(html_content) >= min_content_length:
                        logger.debug(f"Successfully fetched {url} with session.get ({len(html_content)} chars)")
                        return html_content
                    else:
                        logger.warning(f"Session.get returned insufficient content for {url} ({len(html_content) if html_content else 0} chars)")
                else:
                    logger.warning(f"Session.get failed for {url} with status {response.status}")
        except Exception as e:
            logger.warning(f"Session.get failed for {url}: {e}")
        
        # Second try: Use curl as fallback
        try:
            logger.debug(f"Attempting to fetch {url} with curl fallback")
            html_content = await self._fetch_with_curl(url)
            if html_content and len(html_content) >= min_content_length:
                logger.debug(f"Successfully fetched {url} with curl ({len(html_content)} chars)")
                return html_content
            else:
                logger.warning(f"Curl fallback returned insufficient content for {url} ({len(html_content) if html_content else 0} chars)")
        except Exception as e:
            logger.warning(f"Curl fallback failed for {url}: {e}")
        
        logger.error(f"All fetching methods failed for {url}")
        return None
    
    async def _fetch_with_curl(self, url: str) -> Optional[str]:
        """Fetch page content using curl command."""
        try:
            # Get proxy arguments
            proxy_args = self._get_curl_proxy_args()
            
            # Build curl command
            cmd = [
                "curl", "-L", "-s", "-S", "--compressed", "--max-time", "60",
                "--retry", "3", "--retry-delay", "2",
            ]
            
            # Add proxy arguments if configured
            cmd.extend(proxy_args)
            
            # Add URL
            cmd.append(url)
            
            logger.debug(f"Executing curl command: {' '.join(cmd[:10])}... {url}")
            
            # Execute curl command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Curl command failed with return code {result.returncode}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Curl command timed out for {url}")
            return None
        except Exception as e:
            logger.error(f"Curl command failed for {url}: {e}")
            return None
    
    
    async def _scrape_single_article_markdown(self, url: str) -> Optional[Dict]:
        """Scrape content from a single article page using crawl4ai for markdown conversion."""
        temp_file = None
        try:
            # First, fetch HTML content using existing method
            html_content = await self._fetch_page_content(url)
            if not html_content:
                logger.warning(f"Failed to fetch HTML content for {url}")
                return None
            
            # Create a temporary file to store HTML content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_file = f.name
            
            logger.info(f"Converting HTML file to markdown for {url},temp_file: {temp_file}")

            # Use crawl4ai to convert the temporary HTML file to markdown
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=f"file://{temp_file}",
                    bypass_cache=True
                )
                
                if result.success and result.markdown:
                    return {
                        'url': url,
                        'content': result.markdown,
                    }
                else:
                    logger.warning(f"crawl4ai failed to convert HTML file for {url}: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                    return None
                
        except Exception as e:
            logger.warning(f"Error scraping {url} with crawl4ai: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {e}")


    async def _scrape_single_article(self, url: str) -> Optional[Dict]:
        """Scrape content from a single article page using unified scraping logic."""
        try:
            # Try session.get first, fallback to curl if needed
            html_content = await self._fetch_page_content(url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
                element.decompose()
            
            # Find article content
            content_element = None
            selectors = [
                # Modern websites (Wiz.io, etc.)
                'article',
                '[data-layout="content"]',
                '.prose',
                '.content',
                '.article-content',
                
                # Traditional selectors
                '.post-content',
                '.entry-content',
                '.article-content',
                'main main',
                '[itemprop="articleBody"]',
                '.blog-post-content',
                
                # Additional fallbacks
                '.post-body',
                '.entry-body',
                '.story-content',
                '[role="main"] article',
                'section[class*="content"]'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element and len(element.get_text(strip=True)) > 50:
                    content_element = element
                    # logger.debug(f"Found content element: {content_element}")
                    break
            
            # If no specific content found, try to find the largest text block
            if not content_element:
                content_element = self._find_largest_text_block(soup)
                logger.debug(f"Found largest text block: {content_element}")
            
            if not content_element:
                return None
            
            # Extract content
            content = self._clean_text(content_element.get_text(separator=' ', strip=True))
            # logger.debug(f"after clean text content: {content}")
            
            # Extract title - try multiple selectors for different site structures
            title = None
            title_selectors = [
                'h1',  # Most common
                'h2',  # Some sites use h2 for main title
                'h3',  # Wiz.io uses h3 for article titles
                'title',  # Fallback to page title
                '.article-title',
                '.post-title',
                '.entry-title',
                '[class*="title"]'
            ]
            
            # Try to find the best title by looking for the most specific one
            best_title = None
            best_score = 0
            logger.info(f"Trying to find the best title from {url}")
            for selector in title_selectors:
                titles = soup.select(selector)
                logger.debug(f"Found {len(titles)} titles with selector: {selector}")

                for title_elem in titles:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and len(title_text) > 10:  # Must be substantial
                        # Score based on specificity and position
                        score = 0
                        if selector == 'h1':
                            score += 10
                        elif selector == 'h2':
                            score += 8
                        elif selector == 'h3':
                            score += 6
                        elif selector == 'title':
                            score += 4
                        else:
                            score += 2
                        
                        # logger.debug(f"Found title: {title_text}, selector: {selector}, score: {score}, best_score: {best_score}")
                        if score > best_score:
                            best_score = score
                            best_title = title_elem
            
            title_text = best_title.get_text(strip=True) if best_title else "Untitled"
            
            # Extract publish date if possible
            date_el = soup.find('time') or soup.find('span', class_=re.compile('date', re.I))
            publish_date = None
            if date_el:
                date_text = date_el.get('datetime') or date_el.get_text()
                try:
                    publish_date = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    pass
            
            return {
                'url': url,
                'title': title_text,
                'content': content,
                'publish_date': publish_date,
            }
                
        except Exception:
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text content."""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common site navigation text
        patterns_to_remove = [
            r'Original story from.*',
            r'Read more.*',
            r'Continue reading.*',
            r'View comments.*',
            r'Share this:\w+',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def _generate_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def is_cached(self, url: str) -> bool:
        """Check if URL is cached."""
        key = self._generate_cache_key(url)
        return key in self._cache and (datetime.now() - self._cache[key].get('timestamp', datetime.now())).seconds < self.settings.cache_ttl_minutes * 60
    
    async def _scrape_with_scira_api(self, url: str, max_articles: int) -> List[Article]:
        """Scrape using Scira.ai API for Aqua Security."""
        try:
            # Create a prompt to get recent articles from Aqua Security
            prompt = self._create_scira_prompt(url, max_articles)
            
            # Prepare API request with headers similar to requests
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.settings.scira_api_key,
                "User-Agent": "python-requests/2.31.0",  # Match requests library
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",  # Support Brotli encoding
                "Connection": "keep-alive"
            }
            
            payload = {
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            }
            
            logger.info(f"Using Scira.ai API to scrape {url}")
            
            # Create a separate session for Scira.ai API to avoid conflicts
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as api_session:
                async with api_session.post(
                    self.settings.scira_api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    logger.info(f"Scira.ai API response status: {response.status}")
                    logger.info(f"Scira.ai API response headers: {dict(response.headers)}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Scira.ai API error response: {error_text}")
                        raise WebScrapingError(f"Scira.ai API error: HTTP {response.status} - {error_text}")
                    
                    data = await response.json()
                    articles_text = data.get("text", "")
                    
                    if not articles_text:
                        logger.warning("No content returned from Scira.ai API")
                        return []
                    
                    # Parse the response to extract articles
                    articles = self._parse_scira_response(articles_text, url)
                    
                    logger.info(f"Successfully scraped {len(articles)} articles using Scira.ai API")
                    return articles[:max_articles]
                
        except Exception as e:
            logger.error(f"Scira.ai API scraping failed: {e}")
            raise WebScrapingError(f"Scira.ai API scraping failed: {str(e)}")
    
    def _create_scira_prompt(self, url: str, max_articles: int) -> str:
        """Create a prompt for Scira.ai API to get recent articles."""
        return f"Find {max_articles} recent articles from {url}. Return as JSON array with title, url, content fields."
    
    def _parse_scira_response(self, response_text: str, base_url: str) -> List[Article]:
        """Parse Scira.ai API response into Article objects."""
        articles = []
        
        try:
            # Try to extract JSON from the response
            # Look for JSON array in the response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                articles_data = json.loads(json_str)
                
                for article_data in articles_data:
                    try:
                        # Extract company name from URL
                        company_name = self._extract_company_name(base_url)
                        
                        # Parse publish date if available
                        publish_date = None
                        if article_data.get('publish_date'):
                            try:
                                publish_date = datetime.strptime(article_data['publish_date'], '%Y-%m-%d')
                            except ValueError:
                                pass
                        
                        article = Article(
                            url=article_data.get('url', ''),
                            title=article_data.get('title', ''),
                            content=article_data.get('content', ''),
                            company_name=company_name,
                            author=article_data.get('author'),
                            publish_date=publish_date,
                            word_count=len(article_data.get('content', '').split())
                        )
                        articles.append(article)
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse article data: {e}")
                        continue
                        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from Scira.ai response: {e}")
            # Fallback: try to extract basic information from text
            articles = self._parse_scira_fallback(response_text, base_url)
        except Exception as e:
            logger.error(f"Error parsing Scira.ai response: {e}")
            
        return articles
    
    def _parse_scira_fallback(self, response_text: str, base_url: str) -> List[Article]:
        """Fallback parsing when JSON parsing fails."""
        articles = []
        
        # Try to extract article information using regex patterns
        # This is a basic fallback - in practice, the API should return proper JSON
        
        # Look for article titles and URLs in the text
        title_pattern = r'Title[:\s]+(.+?)(?:\n|$)'
        url_pattern = r'URL[:\s]+(https?://[^\s]+)'
        
        titles = re.findall(title_pattern, response_text, re.IGNORECASE | re.MULTILINE)
        urls = re.findall(url_pattern, response_text, re.IGNORECASE | re.MULTILINE)
        
        # Create basic articles from extracted information
        for i, title in enumerate(titles):
            url = urls[i] if i < len(urls) else base_url
            company_name = self._extract_company_name(base_url)
            
            article = Article(
                url=url,
                title=title.strip(),
                content="Content not available in fallback parsing",
                company_name=company_name,
                author=None,
                publish_date=None,
                word_count=0
            )
            articles.append(article)
            
        return articles
    
    async def _scrape_with_curl(self, url: str, max_articles: int) -> List[Article]:
        """Scrape using curl command as fallback method."""
        try:
            logger.info(f"Using curl to scrape {url}")
            
            # Get proxy settings
            proxy_args = self._get_curl_proxy_args()
            
            # Build curl command
            curl_cmd = [
                "curl",
                "-L",  # Follow redirects
                "-s",  # Silent mode
                "-S",  # Show errors
                "--compressed",  # Support compression
                "--max-time", "60",  # 60 second timeout
                "--retry", "3",  # Retry 3 times
                "--retry-delay", "2"  # 2 second delay between retries
            ]
            
            # Add proxy if configured
            if proxy_args:
                curl_cmd.extend(proxy_args)
            
            # Add URL
            curl_cmd.append(url)
            
            logger.debug(f"Executing curl command: {' '.join(curl_cmd)}")
            
            # Execute curl command
            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = f"Curl command failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr}"
                raise WebScrapingError(error_msg)
            
            html_content = result.stdout
            # logger.debug(f"Curl returned HTML content: {html_content}")
            if not html_content:
                raise WebScrapingError("Curl returned empty content")
            
            # Parse HTML content
            articles = await self._parse_html_content(html_content, url, max_articles)
            
            logger.info(f"Successfully scraped {len(articles)} articles using curl.articles: {articles}")
            return articles
            
        except subprocess.TimeoutExpired:
            logger.error("Curl command timed out")
            raise WebScrapingError("Curl command timed out")
        except FileNotFoundError:
            logger.error("Curl command not found. Please install curl.")
            raise WebScrapingError("Curl command not found. Please install curl.")
        except Exception as e:
            logger.error(f"Curl scraping failed: {e}")
            raise WebScrapingError(f"Curl scraping failed: {str(e)}")
    
    def _get_curl_proxy_args(self) -> List[str]:
        """Get curl proxy arguments based on settings."""
        proxy_args = []
        
        # Check settings first
        if self.settings.enable_proxy and self.settings.proxy_url:
            proxy_url = self.settings.proxy_url
            if self.settings.proxy_username and self.settings.proxy_password:
                # Extract protocol and host:port from proxy_url
                if proxy_url.startswith(('http://', 'https://')):
                    protocol = proxy_url.split('://')[0]
                    host_port = proxy_url.split('://')[1]
                    proxy_args.extend([
                        "--proxy", f"{protocol}://{self.settings.proxy_username}:{self.settings.proxy_password}@{host_port}"
                    ])
                else:
                    proxy_args.extend(["--proxy", proxy_url])
            else:
                proxy_args.extend(["--proxy", proxy_url])
        else:
            # Check environment variables
            http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
            https_proxy = os.getenv('https_proxy') or os.getenv('HTTPS_PROXY')
            
            if http_proxy:
                proxy_args.extend(["--proxy", http_proxy])
            elif https_proxy:
                proxy_args.extend(["--proxy", https_proxy])
        
        return proxy_args
    
    async def _parse_html_content(self, html_content: str, base_url: str, max_articles: int) -> List[Article]:
        """Parse HTML content to extract articles using unified parsing logic."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            company_name = self._extract_company_name(base_url)
            
            # Use the unified article extraction logic (curl method - no full content scraping)
            articles = await self._extract_articles_from_html(soup, base_url, max_articles, company_name, scrape_full_content=True)
            
            # If no articles found, try to extract from page content
            if not articles:
                logger.warning("No article links found, attempting to extract from page content")
                articles = self._extract_articles_from_content(soup, base_url, max_articles)
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to parse HTML content: {e}")
            raise WebScrapingError(f"Failed to parse HTML content: {str(e)}")
    
    async def _extract_articles_from_html(self, soup: BeautifulSoup, base_url: str, max_articles: int, company_name: str, scrape_full_content: bool = True) -> List[Article]:
        """Unified method to extract articles from HTML content."""
        articles = []
        
        try:
            # Find article links using the existing logic
            article_links = self._find_article_links(soup, base_url)
            logger.info(f"Found {len(article_links)} article links,article_links: {article_links}")
            
            # Process each article link
            for link_url in article_links[:max_articles]:
                try:
                    if scrape_full_content:
                        # This is called from _scrape_generic_blog - scrape full content
                        article_data = await self._scrape_single_article(link_url)
                        
                        if article_data:
                            article = Article(
                                url=article_data['url'],
                                title=article_data['title'],
                                content=article_data['content'],
                                company_name=company_name,
                                author=article_data.get('author'),
                                publish_date=article_data.get('publish_date'),
                                word_count=len(article_data['content'].split())
                            )
                            articles.append(article)
                    else:
                        # This is called from curl method - extract basic info only
                        # Parse the link URL to get title from the page
                        title = self._extract_title_from_url(link_url, soup)
                        
                        article = Article(
                            url=link_url,
                            title=title or "Untitled Article",
                            content="Content not available - use curl to fetch individual articles",
                            company_name=company_name,
                            author=None,
                            publish_date=None,
                            word_count=0
                        )
                        articles.append(article)
                        
                except Exception as e:
                    logger.warning(f"Failed to process article link {link_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to extract articles from HTML: {e}")
            
        return articles
    
    def _extract_title_from_url(self, url: str, soup: BeautifulSoup) -> str:
        """Extract title for a URL from the page content."""
        try:
            # Try to find a link with this URL and get its text
            link = soup.find('a', href=url)
            if link:
                return link.get_text(strip=True)
            
            # Try to find by partial URL match
            for link in soup.find_all('a', href=True):
                if url in link.get('href', '') or link.get('href', '') in url:
                    return link.get_text(strip=True)
                    
        except Exception as e:
            logger.debug(f"Failed to extract title for {url}: {e}")
            
        return None
    
    def _extract_articles_from_content(self, soup: BeautifulSoup, base_url: str, max_articles: int) -> List[Article]:
        """Extract articles from page content when no clear article links are found."""
        articles = []
        company_name = self._extract_company_name(base_url)
        
        try:
            # Look for headings that might be article titles
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            
            for heading in headings[:max_articles]:
                title = heading.get_text(strip=True)
                if len(title) < 10:  # Skip short titles
                    continue
                
                # Try to find a link near this heading
                article_url = base_url
                link = heading.find('a', href=True)
                if link:
                    article_url = urljoin(base_url, link.get('href', ''))
                
                article = Article(
                    url=article_url,
                    title=title,
                    content="Content not available - use curl to fetch individual articles",
                    company_name=company_name,
                    author=None,
                    publish_date=None,
                    word_count=0
                )
                articles.append(article)
                
        except Exception as e:
            logger.warning(f"Failed to extract articles from content: {e}")
        
        return articles