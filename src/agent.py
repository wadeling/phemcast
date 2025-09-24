"""LangGraph agent for industry news aggregation and analysis."""
import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from settings import Settings, load_settings
from models import AgentState, Article, CompanyInsights
from tools import scrape_articles, analyze_content, generate_weekly_report
from web_scraper import AsyncWebScraper
from report_generator import ReportGenerator
from email_service import EmailService


logger = logging.getLogger(__name__)


class IndustryNewsAgent:
    """Main LangGraph-based agent for industry news aggregation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.graph = self._create_workflow()
        
    def _create_workflow(self) -> StateGraph:
        """Create the complete LangGraph workflow."""
        
        # Define workflow nodes
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("validate_urls", self._validate_urls)
        workflow.add_node("scrape_articles", self._scrape_articles)
        workflow.add_node("analyze_content", self._analyze_content)
        workflow.add_node("generate_reports", self._generate_reports)
        
        # Add edges (workflow flow)
        workflow.set_entry_point("validate_urls")
        workflow.add_edge("validate_urls", "scrape_articles")
        workflow.add_edge("scrape_articles", "analyze_content")
        workflow.add_edge("analyze_content", "generate_reports")
        workflow.add_edge("generate_reports", END)
        
        # Compile workflow
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)
    
    async def run_workflow(
        self, 
        task_id: str,
        urls: List[str], 
        max_articles: int = 5,
        company_configs: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Run the complete industry news workflow.
        
        Args:
            urls: List of blog URLs to process
            email_recipients: List of email addresses for report delivery
            max_articles: Maximum articles per blog
            
        Returns:
            Complete workflow result
        """
        if not urls:
            return {
                "status": "error",
                "message": "No URLs provided",
                "errors": ["No URLs provided"]
            }
        
        try:
            initial_state = {
                "task_id": task_id,
                "urls": urls,
                "max_articles": max_articles,
                "company_configs": company_configs or [],
                "processing_status": "starting",
                "errors": [],
                "total_tokens_used": 0,
                "progress": {"total": len(urls), "completed": 0},
                "logs": ["🎯 Starting report generation for {} URLs".format(len(urls))],
                "total_urls": len(urls),
                "total_articles": 0
            }
            
            logger.info(f"Starting workflow with {len(urls)} URLs, max_articles: {max_articles},company_configs: {company_configs}")
            
            # Run the workflow without checkpointing for background processing
            config = {"configurable": {"thread_id": f"background_{datetime.now().timestamp()}"}}
            # Use asyncio.to_thread to avoid blocking the event loop
            import asyncio
            
            # Create a wrapper function that runs the async workflow in a thread
            def run_workflow_sync():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.graph.ainvoke(initial_state, config=config))
                finally:
                    loop.close()
            
            final_state = await asyncio.to_thread(run_workflow_sync)
            
            # 获取报告路径，包括音频
            report_paths = {}
            if final_state.get("report_path_md"):
                report_paths["markdown"] = final_state.get("report_path_md", "")
            if final_state.get("report_path_pdf"):
                report_paths["pdf"] = final_state.get("report_path_pdf", "")

            if final_state.get("report_path_audio"):
                report_paths["audio"] = final_state.get("report_path_audio", "")
            else:
                report_paths["audio"] = ""
                logger.warning(f"No audio data found in final_state: {final_state}")
           
            logger.info(f"Final report_paths: {report_paths}")
            
            return {
                "status": final_state.get("processing_status", "completed"),
                "errors": final_state.get("errors", []),
                "total_articles": len(final_state.get("articles", [])),
                "total_urls": final_state.get("total_urls", 0),
                "report_paths": report_paths,
                "total_tokens_used": final_state.get("total_tokens_used", 0),
                "logs": final_state.get("logs", []),
                "processing_time": final_state.get("processing_time", 0),
                "articles": final_state.get("articles", [])  # Include articles for aggregation
            }
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "errors": [str(e)]
            }
    
    async def _validate_urls(self, state: AgentState) -> AgentState:
        """Validate and normalize URLs."""
        urls = state.get("urls", [])
        validated_urls = []
        errors = state.get("errors", [])
        
        for url in urls:
            try:
                # Basic URL validation and normalization
                if not (url.startswith("http://") or url.startswith("https://")):
                    url = "https://" + url
                validated_urls.append(url)
            except Exception as e:
                errors.append(f"Invalid URL '{url}': {str(e)}")
        
        state.update({
            "urls": validated_urls,
            "processing_status": "urls_validated",
            "errors": errors,
            "progress": {"total": len(validated_urls), "completed": 0}
        })
        
        return state
    
    
    async def _scrape_detailed_content(self, articles: List[Dict]) -> List[Dict]:
        """Scrape detailed content for a list of articles."""
        if not articles:
            return articles
            
        logger.info(f"Scraping detailed content for {len(articles)} articles")
        detailed_articles = []
        
        # Use AsyncWebScraper as context manager to properly initialize session
        async with AsyncWebScraper(self.settings) as web_scraper:
            for article in articles:
                try:
                    # Scrape detailed content from the article URL
                    detailed_content = await web_scraper._scrape_single_article_markdown(article["url"])
                    if detailed_content:
                        # Merge the detailed content with the original article data
                        article.update({
                            "content": detailed_content.get("content", article.get("content", "")),
                            "title": detailed_content.get("title", article.get("title", "")),
                            "published": detailed_content.get("publish_date", article.get("published", ""))
                        })
                        logger.debug(f"Successfully scraped content for: {article['title']}, content: {article['content']}")
                    else:
                        logger.warning(f"Failed to scrape detailed content for: {article['url']}")
                except Exception as e:
                    logger.warning(f"Error scraping detailed content for {article['url']}: {e}")
                
                detailed_articles.append(article)
        
        logger.info(f"Completed detailed content scraping for {len(detailed_articles)} articles")
        return detailed_articles
    
    async def _scrape_articles(self, state: AgentState) -> AgentState:
        """Scrape articles from validated URLs using company configurations."""
        urls = state.get("urls", [])
        max_articles = state.get("max_articles", 5)
        company_configs = state.get("company_configs", [])
        logger.debug(f"Scraping articles from {len(urls)} URLs, max_articles: {max_articles},company_configs: {company_configs}")
        
        try:
            article_objects = []
            scrape_errors = []
            
            # Process each company configuration
            for company_config in company_configs:
                company_name = company_config["name"]
                company_url = company_config["url"]
                is_rss = company_config["rss"]
                
                logger.info(f"Processing {company_name} - URL: {company_url}, RSS: {is_rss}")
                
                # Step 1: Get basic article information
                if is_rss:
                    # Use RSS feed to get latest article links
                    articles = await self._fetch_rss_articles(company_url, max_articles)
                else:
                    # Use regular scraping to get articles
                    articles = await self._fetch_blog_articles(company_url, max_articles)
                
                logger.info(f"Found {len(articles)} articles for {company_name}")
                
                if not articles:
                    logger.warning(f"No articles found for {company_name}")
                    continue
                
                # Step 2: Scrape detailed content for this company's articles
                detailed_articles = await self._scrape_detailed_content(articles)
                
                # Step 3: Convert to Article objects with known company_name
                from models import Article
                for article_data in detailed_articles:
                    # Convert published date format
                    publish_date = None
                    if article_data.get("published"):
                        try:
                            from datetime import datetime
                            publish_date = datetime.fromisoformat(article_data["published"].replace('Z', '+00:00'))
                        except (ValueError, TypeError):
                            pass
                    elif article_data.get("publish_date"):
                        publish_date = article_data["publish_date"]
                    
                    article = Article(
                        title=article_data.get("title", ""),
                        url=article_data.get("url", ""),
                        company_name=company_name,  # Use the known company name
                        publish_date=publish_date,
                        summary=article_data.get("summary", ""),
                        content=article_data.get("content", ""),
                        word_count=len(article_data.get("content", "").split())
                    )
                    article_objects.append(article)
                
                logger.info(f"Successfully processed {len(detailed_articles)} articles for {company_name}")
            
            if not article_objects:
                raise Exception("No articles found for any company")
            
            state.update({
                "articles": article_objects,
                "processing_status": "articles_scraped",
                "errors": state.get("errors", []) + scrape_errors,
                "progress": {"total": len(urls), "completed": len(urls)},
                "logs": state.get("logs", []) + [
                    f"✅ Scraped {len(article_objects)} articles from {len(company_configs)} companies",
                    f"📈 Company processing: 100% complete"
                ],
                "total_articles": len(article_objects)
            })
            
            logger.info(f"Scraped {len(article_objects)} articles from {len(company_configs)} companies")
            logger.info(f"State after scraping - articles count: {len(state.get('articles', []))}, status: {state.get('processing_status')}")
            
        except Exception as e:
            logger.error(f"Article scraping failed: {str(e)}")
            state.update({
                "processing_status": "error",
                "errors": state.get("errors", []) + [f"Scraping failed: {str(e)}"],
                "logs": state.get("logs", []) + [f"❌ Scraping error: {str(e)}"]
            })
        
        return state
    
    async def _analyze_content(self, state: AgentState) -> AgentState:
        """Analyze scraped articles using AI."""
        articles = state.get("articles", [])
        
        if not articles:
            state.update({
                "processing_status": "error",
                "errors": state.get("errors", []) + ["No articles to analyze"]
            })
            return state
        
        try:
            state["logs"] = state.get("logs", []) + [f"🤖 Starting AI analysis for {len(articles)} articles"]
            
            # Import here to avoid circular dependencies
            from tools import AIContentAnalysisTool
            
            analyzer = AIContentAnalysisTool(self.settings)
            # Call _run directly to avoid BaseTool.run() issues
            analyzed_articles = analyzer._run(articles=articles)
            
            # Update articles with analysis
            state.update({
                "articles": analyzed_articles,
                "processing_status": "content_analyzed",
                "total_tokens_used": state.get("total_tokens_used", 0) + len(articles) * 500,
                "logs": state.get("logs", []) + [
                    f"✅ AI analysis complete: {len(analyzed_articles)} articles analyzed",
                    f"🔢 Estimated tokens used: {len(articles) * 500}"
                ]
            })
            
            logger.info(f"Analyzed {len(analyzed_articles)} articles")
            
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            state.update({
                "processing_status": "error",
                "errors": state.get("errors", []) + [f"Analysis failed: {str(e)}"],
                "logs": state.get("logs", []) + [f"❌ AI analysis failed: {str(e)}"]
            })
        
        return state
    
    
    async def _generate_reports(self, state: AgentState) -> AgentState:
        """Generate final reports."""
        articles = state.get("articles", [])
        
        logger.info(f"Starting report generation with {len(articles)} articles")
        
        if not articles:
            logger.warning("No articles available for report generation")
            state["report_path_md"] = ""
            state["report_path_pdf"] = ""
            state["report_path_audio"] = {}
            state["processing_status"] = "error"
            return state
        
        try:
            start_time = datetime.now()
            total_articles = len(articles)
            
            state["logs"] = state.get("logs", []) + [f"📝 Starting report generation for {total_articles} articles"]
            
            report_generator = ReportGenerator(self.settings)
            logger.info(f"Calling ReportGenerator.generate_all_reports with {len(articles)} articles")
            report_paths = await report_generator.generate_all_reports(
                articles, {}
            )
            
            logger.info(f"ReportGenerator returned paths: {report_paths},audio_data: {report_paths.get('audio', 'Not found')}")
            
            # 准备基础更新数据
            processing_time = (datetime.now() - start_time).total_seconds()
            base_update = {
                "total_articles": total_articles,
                "execution_date": datetime.now(),
                "report_path_md": report_paths.get("markdown", ""),
                "report_path_pdf": report_paths.get("pdf", ""),
                "processing_status": "completed",
                "processing_time": processing_time
            }
            
            # 准备日志
            logs = state.get("logs", []) + [
                f"✅ Reports generated: {list(report_paths.keys())}",
                f"⏱️ Report generation time: {processing_time:.1f}s"
            ]

            # 获取音频数据
            audio_data = report_paths.get("audio", {})
            audio_success = audio_data and isinstance(audio_data, dict) and audio_data.get("success")
            if audio_success:
                logger.info(f"Audio generation successful: {audio_data.get('access_token', 'No token')}")
                base_update.update({
                    "report_path_audio": audio_data.get("audio_path", ""),
                    "logs": logs + [f"🎧 Audio report: {audio_data.get('access_token', 'No token')}"]
                })
            else:
                logger.warning(f"Audio generation failed or not available: {audio_data}")
                base_update.update({
                    "report_path_audio": "",
                    "logs": logs + ["⚠️ No audio report generated"]
                })
            
            state.update(base_update)
            
            logger.info(f"Generated reports: {list(report_paths.keys())}")
            logger.info(f"State after report generation - report_path_audio: {state.get('report_path_audio')}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            state.update({
                "processing_status": "error",
                "errors": state.get("errors", []) + [f"Report generation failed: {str(e)}"],
                "logs": state.get("logs", []) + [f"❌ Report generation failed: {str(e)}"]
            })
        
        return state
    
    
    async def _fetch_rss_articles(self, rss_url: str, max_articles: int) -> List[Dict]:
        """Fetch articles from RSS feed with curl fallback."""
        try:
            import feedparser
            
            logger.info(f"Fetching RSS articles from {rss_url}")
            
            # Try feedparser first
            try:
                feed = feedparser.parse(rss_url)
                if not feed.entries:
                    raise Exception("No entries found in RSS feed")
            except Exception as e:
                logger.warning(f"feedparser failed for {rss_url}: {e}, trying curl fallback")
                # Fallback to curl
                feed = await self._fetch_rss_with_curl(rss_url)
                if not feed or not feed.entries:
                    raise Exception(f"Both feedparser and curl failed for {rss_url}")
            
            articles = []
            for entry in feed.entries:
                # Extract title and clean it
                title = entry.get("title", "")
                if title and hasattr(title, 'strip'):
                    title = title.strip()
                
                # Extract URL
                url = entry.get("link", "")
                
                # Extract published date (try different field names)
                published = entry.get("published", "") or entry.get("pubDate", "")
                
                # Extract summary/description (try different field names)
                summary = entry.get("summary", "") or entry.get("description", "")
                if summary and hasattr(summary, 'strip'):
                    summary = summary.strip()
                
                # Extract content (try different field names)
                content = ""
                if hasattr(entry, 'content') and entry.content:
                    # Handle content as a list of dictionaries
                    if isinstance(entry.content, list) and len(entry.content) > 0:
                        content = entry.content[0].get('value', '') if hasattr(entry.content[0], 'get') else str(entry.content[0])
                    else:
                        content = str(entry.content)
                elif hasattr(entry, 'content_encoded') and entry.content_encoded:
                    # Handle content_encoded as a list
                    if isinstance(entry.content_encoded, list) and len(entry.content_encoded) > 0:
                        content = entry.content_encoded[0]
                    else:
                        content = str(entry.content_encoded)
                elif hasattr(entry, 'get'):
                    # Try to get content from namespaced fields
                    content = entry.get("content:encoded", "") or entry.get("content", "")
                
                # Clean content if it's a string
                if content and hasattr(content, 'strip'):
                    content = content.strip()
                
                article = {
                    "title": title,
                    "url": url,
                    "published": published,
                    "summary": summary,
                    "content": content
                }
                articles.append(article)
            
            # Sort articles by published date (newest first)
            articles = self._sort_articles_by_date(articles)
            
            # Take only the most recent max_articles
            articles = articles[:max_articles]
            
            logger.info(f"Found {len(articles)} RSS articles (sorted by date, newest first)")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch RSS articles from {rss_url}: {e}")
            return []

    async def _fetch_blog_articles(self, blog_url: str, max_articles: int) -> List[Dict]:
        """Fetch articles from blog using crawl4ai or curl fallback with LLM extraction."""
        try:
            logger.info(f"Fetching blog articles from {blog_url}")
            
            # Try crawl4ai first to get markdown content
            markdown_content = await self._fetch_markdown_with_crawl4ai(blog_url)
            if markdown_content:
                logger.info("Successfully fetched markdown content with crawl4ai")
            else:
                # Fallback to curl + html2markdown
                logger.info("crawl4ai failed, trying curl + html2markdown fallback")
                markdown_content = await self._fetch_markdown_with_curl(blog_url)
                if markdown_content:
                    logger.info("Successfully fetched markdown content with curl + html2markdown")
            
            # Extract articles using LLM if we have markdown content
            if markdown_content:
                articles = await self._extract_articles_with_llm(markdown_content, blog_url, max_articles)
                if articles:
                    logger.info(f"Successfully extracted {len(articles)} articles with LLM")
                    return articles
                else:
                    logger.warning("LLM extraction returned no articles")
            else:
                logger.warning(f"Failed to fetch content from {blog_url} with both methods")
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch blog articles from {blog_url}: {e}")
            return []

    async def _fetch_markdown_with_crawl4ai(self, url: str) -> str:
        """Fetch markdown content using crawl4ai library."""
        try:
            from crawl4ai import AsyncWebCrawler
            
            async with AsyncWebCrawler(verbose=True) as crawler:
                # Crawl the page
                result = await crawler.arun(url=url)
                
                if result.success and result.markdown:
                    logger.info(f"Successfully fetched markdown content with crawl4ai from {url}")
                    return result.markdown
                else:
                    logger.warning(f"crawl4ai failed to get markdown content from {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"crawl4ai markdown fetch failed: {e}")
            return None

    async def _fetch_markdown_with_curl(self, url: str) -> str:
        """Fetch HTML content with curl and convert to markdown."""
        try:
            import html2markdown
            
            # Use unified curl method to get HTML content
            html_content = await self._fetch_content_with_curl(url)
            
            if not html_content:
                logger.error("curl returned empty content")
                return None
            
            # Convert HTML to markdown
            markdown_content = html2markdown.convert(html_content)
            
            if markdown_content and markdown_content.strip():
                logger.info(f"Successfully converted HTML to markdown from {url}")
                return markdown_content
            else:
                logger.warning(f"html2markdown conversion resulted in empty content from {url}")
                return None
                
        except Exception as e:
            logger.error(f"curl + html2markdown failed: {e}")
            return None

    async def _extract_articles_with_llm(self, markdown_content: str, blog_url: str, max_articles: int) -> List[Dict]:
        """Use ArticleExtractionTool to extract article URLs and titles from markdown content."""
        try:
            from tools import ArticleExtractionTool
            
            # Create tool instance
            extraction_tool = ArticleExtractionTool(self.settings)
            
            # Use the tool to extract articles
            articles = await extraction_tool._arun(markdown_content, blog_url, max_articles)
            
            logger.info(f"ArticleExtractionTool extracted {len(articles)} articles from {blog_url}")
            return articles
                
        except Exception as e:
            logger.error(f"Article extraction failed: {e}")
            return []

    async def _fetch_with_crawl4ai(self, url: str, max_articles: int) -> List[Dict]:
        """Fetch articles using crawl4ai library."""
        try:
            from crawl4ai import AsyncWebCrawler
            from bs4 import BeautifulSoup
            
            articles = []
            
            async with AsyncWebCrawler(verbose=True) as crawler:
                # Crawl the page
                result = await crawler.arun(url=url)
                
                if result.success and result.html:
                    # Parse the HTML content to extract articles
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # Look for article links (this is a simplified approach)
                    article_links = soup.find_all('a', href=True)
                    
                    for link in article_links[:max_articles]:
                        href = link.get('href')
                        title = link.get_text(strip=True)
                        if href and title and len(title) > 10:  # Basic filter for meaningful links
                            # Make absolute URL
                            if href.startswith('/'):
                                href = url.rstrip('/') + href
                            elif not href.startswith('http'):
                                href = url.rstrip('/') + '/' + href
                            
                            article = {
                                "title": title,
                                "url": href,
                                "published": "",
                                "summary": "",
                                "content": ""
                            }
                            articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"crawl4ai failed: {e}")
            return []

    async def _fetch_with_curl(self, url: str, max_articles: int) -> List[Dict]:
        """Fetch articles using curl as fallback."""
        try:
            from bs4 import BeautifulSoup
            
            # Use unified curl method
            html_content = await self._fetch_content_with_curl(url)
            
            if not html_content:
                logger.error("curl returned empty content")
                return []
            
            # Parse HTML to extract articles
            soup = BeautifulSoup(html_content, 'html.parser')
            articles = []
            
            # Look for article links
            article_links = soup.find_all('a', href=True)
            
            for link in article_links[:max_articles]:
                href = link.get('href')
                title = link.get_text(strip=True)
                if href and title and len(title) > 10:  # Basic filter for meaningful links
                    # Make absolute URL
                    if href.startswith('/'):
                        href = url.rstrip('/') + href
                    elif not href.startswith('http'):
                        href = url.rstrip('/') + '/' + href
                    
                    article = {
                        "title": title,
                        "url": href,
                        "published": "",
                        "summary": "",
                        "content": ""
                    }
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"curl fallback failed: {e}")
            return []

    async def _fetch_rss_with_curl(self, rss_url: str):
        """Fetch RSS feed using curl as fallback."""
        try:
            import feedparser
            
            logger.info(f"Fetching RSS with curl from {rss_url}")
            
            # Use unified curl method
            content = await self._fetch_content_with_curl(
                rss_url, 
                headers={'Accept': 'application/rss+xml, application/xml, text/xml'}
            )
            
            if not content:
                logger.error("curl returned empty content")
                return None
            
            # Parse the XML content with feedparser
            feed = feedparser.parse(content)
            
            if not feed.entries:
                logger.error("No entries found in curl-fetched RSS feed")
                return None
            
            logger.info(f"Successfully fetched RSS with curl, found {len(feed.entries)} entries")
            return feed
            
        except Exception as e:
            logger.error(f"RSS curl fallback failed: {e}")
            return None

    async def _fetch_content_with_curl(self, url: str, headers: dict = None) -> str:
        """Unified curl method for fetching content with proxy support."""
        try:
            import subprocess
            import tempfile
            
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
                "--retry-delay", "2",  # 2 second delay between retries
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ]
            
            # Add proxy if configured
            if proxy_args:
                curl_cmd.extend(proxy_args)
            
            # Add headers if provided
            if headers:
                for key, value in headers.items():
                    curl_cmd.extend(["--header", f"{key}: {value}"])
            
            # Add URL
            curl_cmd.append(url)
            
            logger.debug(f"Executing curl command: {' '.join(curl_cmd)}")
            
            # Use curl to fetch the content
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
                result = subprocess.run(curl_cmd, stdout=f, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    logger.error(f"curl failed: {result.stderr}")
                    return None
                
                f.seek(0)
                content = f.read()
            
            return content
            
        except Exception as e:
            logger.error(f"curl content fetch failed: {e}")
            return None

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
            import os
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            if http_proxy:
                proxy_args.extend(["--proxy", http_proxy])
            elif https_proxy:
                proxy_args.extend(["--proxy", https_proxy])
        
        return proxy_args

    def _sort_articles_by_date(self, articles: List[Dict]) -> List[Dict]:
        """Sort articles by published date (newest first)."""
        try:
            from datetime import datetime
            import dateutil.parser
            
            def get_sort_key(article):
                published = article.get("published", "")
                if not published:
                    # If no published date, put at the end
                    return datetime.min
                
                try:
                    # Try to parse the date using dateutil
                    parsed_date = dateutil.parser.parse(published)
                    return parsed_date
                except (ValueError, TypeError):
                    # If parsing fails, try to extract year/month/day manually
                    try:
                        # Try common RSS date formats
                        for fmt in [
                            "%a, %d %b %Y %H:%M:%S %Z",
                            "%a, %d %b %Y %H:%M:%S %z",
                            "%a, %d %b %Y %H:%M:%S GMT",
                            "%Y-%m-%d %H:%M:%S",
                            "%Y-%m-%dT%H:%M:%S%z",
                            "%Y-%m-%dT%H:%M:%SZ"
                        ]:
                            try:
                                return datetime.strptime(published, fmt)
                            except ValueError:
                                continue
                        
                        # If all parsing fails, put at the end
                        logger.warning(f"Could not parse date: {published}")
                        return datetime.min
                    except Exception:
                        logger.warning(f"Could not parse date: {published}")
                        return datetime.min
            
            # Sort by published date (newest first)
            sorted_articles = sorted(articles, key=get_sort_key, reverse=True)
            
            logger.debug(f"Sorted {len(sorted_articles)} articles by date")
            return sorted_articles
            
        except Exception as e:
            logger.error(f"Failed to sort articles by date: {e}")
            # Return original list if sorting fails
            return articles


# Convenience function for direct usage
def create_agent(settings: Settings = None) -> IndustryNewsAgent:
    """Factory function to create an agent instance."""
    if settings is None:
        settings = load_settings()
    return IndustryNewsAgent(settings)


# Synchronous convenience wrapper for backward compatibility
def process_urls(
    urls: List[str],
    email_recipients: List[str] = None,
    max_articles: int = 5,
    settings: Settings = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for the async workflow.
    
    Args:
        urls: List of URLs to process
        email_recipients: Email addresses for report delivery
        max_articles: Maximum articles per blog
        settings: Application settings
        
    Returns:
        Workflow result
    """
    if settings is None:
        settings = load_settings()
    
    agent = create_agent(settings)
    return asyncio.run(agent.run_workflow(urls, email_recipients, max_articles))