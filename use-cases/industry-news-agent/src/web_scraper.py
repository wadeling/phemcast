"""Async web scraping with rate limiting and error handling."""
import asyncio
import aiohttp
import feedparser
import re
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import random
import traceback
from datetime import datetime
import hashlib

from .models import Article
from .settings import Settings


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
        self, urls: List[str], max_articles: int = 5
    ) -> Tuple[List[Article], List[str]]:
        """
        Scrape articles from multiple blog URLs with rate limiting.
        
        Args:
            urls: List of blog URLs to scrape
            max_articles: Maximum articles per blog
            
        Returns:
            Tuple of (articles, error_messages)
        """
        articles = []
        errors = []
        
        # Process URLs with delay between requests
        for i, url in enumerate(urls):
            if i > 0:
                await asyncio.sleep(self.settings.request_delay)
            
            try:
                url_articles = await self._scrape_single_blog(url, max_articles)
                articles.extend(url_articles)
            except Exception as e:
                errors.append(f"Error scraping {url}: {str(e)}")
        
        return articles, errors
    
    async def _scrape_single_blog(
        self, url: str, max_articles: int
    ) -> List[Article]:
        """Scrape a single blog/website."""
        try:
            # Normalize URL first
            url = self._normalize_url(url)
            
            # Detect platform and route to appropriate scraper
            if self._is_rss_feed(url):
                return await self._scrape_rss(url, max_articles)
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
            for entry in feed.entries[:max_articles]:
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
        """Scrape generic blog using BeautifulSoup."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise WebScrapingError(f"HTTP {response.status}: {url}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()
                
                articles = []
                company_name = self._extract_company_name(url)
                
                # Try to find blog posts/articles
                article_selectors = [
                    'article',
                    '.post',
                    '.entry-content',
                    '.blog-post',
                    '[itemtype*="BlogPosting"]',
                    '.post-content',
                    'main article',
                    '.article'
                ]
                
                # Find potential article links
                article_links = self._find_article_links(soup, url)
                
                for link in article_links[:max_articles]:
                    try:
                        article_url = urljoin(url, link.get('href', ''))
                        article_data = await self._scrape_single_article(article_url)
                        
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
                            
                    except Exception:
                        continue  # Skip individual article failures
                
                return articles
                
        except Exception as e:
            raise WebScrapingError(f"Generic blog scraping failed: {str(e)}")
    
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
        
        # Common selectors for article links
        selectors = [
            'a[href*="/"]',  # All links
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
                if href and ('http' not in href or base_url in href):
                    links.append(link)
                    if len(links) >= 20:  # Reasonable limit
                        break
            if links:
                break
        
        return links
    
    async def _scrape_single_article(self, url: str) -> Optional[Dict]:
        """Scrape content from a single article page."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Find article content
                content_element = None
                selectors = [
                    'article',
                    '.post-content',
                    '.entry-content',
                    '.article-content',
                    'main main',
                    '[itemprop="articleBody"]',
                    '.blog-post-content'
                ]
                
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element and len(element.get_text(strip=True)) > 50:
                        content_element = element
                        break
                
                if not content_element:
                    return None
                
                # Extract content
                content = self._clean_text(content_element.get_text(separator=' ', strip=True))
                
                # Extract title
                title = soup.find('h1')
                if not title:
                    title = soup.find('title')
                title_text = title.get_text(strip=True) if title else "Untitled"
                
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