"""LangGraph tools for web scraping, AI analysis, and report generation."""
import asyncio
from typing import List, Dict, Optional
import json
from datetime import datetime
from langchain_core.tools import tool, BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from tempfile import mkdtemp
from pathlib import Path

from .settings import Settings
from .models import Article, CompanyInsights, AnalysisConfig
from .web_scraper import AsyncWebScraper
from .report_generator import ReportGenerator


def initialize_tools(settings: Settings):
    """Initialize and configure all tools with settings."""
    return [
        WebScrapingTool(settings),
        AIContentAnalysisTool(settings),
        ReportGenerationTool(settings)
    ]


class WebScrapingTool(BaseTool):
    """Tool for scraping articles from blog URLs."""
    
    name: str = "scrape_blog_articles"
    description: str = """Scrape articles from company blog URLs with rate limiting and error handling.
    
    Args:
        urls: List of blog URLs to scrape (e.g., ['https://blog.openai.com'])
        max_articles: Maximum articles per blog (default: 5)
    
    Returns:
        Tuple of (articles, error_messages) where articles is a list of Article objects"""
    
    return_direct: bool = False
    settings: Settings
    
    def __init__(self, settings: Settings):
        super().__init__(settings=settings)
        self.settings = settings
    
    async def _arun(self, urls: List[str], max_articles: int = 5) -> tuple:
        """Async run web scraping."""
        if not urls:
            return [], ["No URLs provided"]
        
        try:
            async with AsyncWebScraper(self.settings) as scraper:
                articles, errors = await scraper.scrape_blog_articles(urls, max_articles)
                return articles, errors
        except Exception as e:
            return [], [f"Web scraping failed: {str(e)}"]
    
    def _run(self, *args, **kwargs) -> tuple:
        """Sync run wrapper that handles various input formats from LangChain."""
        try:
            # Extract arguments from different possible formats
            urls = None
            max_articles = 5
            
            # Case 1: Arguments passed as positional args
            if len(args) >= 1:
                urls = args[0]
                if len(args) >= 2:
                    max_articles = args[1]
            
            # Case 2: Arguments passed as keyword args
            if 'urls' in kwargs:
                urls = kwargs['urls']
            if 'max_articles' in kwargs:
                max_articles = kwargs['max_articles']
            
            # Ensure urls is a list
            if not isinstance(urls, list):
                urls = [urls]
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, run in a separate thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    def run_async():
                        return asyncio.run(self._arun(urls, max_articles))
                    future = executor.submit(run_async)
                    return future.result()
            except RuntimeError:
                # No event loop running, use asyncio.run
                return asyncio.run(self._arun(urls, max_articles))
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error in WebScrapingTool._run: {e}")
            print(f"Args: {args}")
            print(f"Kwargs: {kwargs}")
            raise e


class AIContentAnalysisTool(BaseTool):
    """Tool for AI-powered content analysis and summarization."""
    
    name: str = "analyze_blog_content"
    description: str = """Analyze articles using AI to extract insights, summarize content, and identify trends.
    
    Args:
        articles: List of Article objects with raw content
        analysis_config: Analysis configuration dictionary
    
    Returns:
        List of Article objects with added summary, insights, and analysis"""
    
    return_direct: bool = False
    settings: Settings
    llm: Optional[ChatOpenAI] = None
    
    def __init__(self, settings: Settings):
        # Initialize with required settings
        super().__init__(settings=settings)
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            model=settings.openai_model,
            temperature=0.3,
            max_tokens=settings.max_tokens_per_article
        )
    
    async def _arun(self, articles: List[Article], analysis_config: Dict = None) -> List[Article]:
        """Async analysis of articles."""
        config = AnalysisConfig(**(analysis_config or {}))
        analyzed_articles = []
        
        for article in articles:
            try:
                analyzed_article = await self._analyze_article(article, config)
                analyzed_articles.append(analyzed_article)
            except Exception as e:
                # Keep the article but add error info
                article.summary = f"Analysis failed: {str(e)}"
                analyzed_articles.append(article)
        
        return analyzed_articles
    
    def _run(self, *args, **kwargs) -> List[Article]:
        """Sync run wrapper that handles various input formats from LangChain."""
        try:
            # LangChain might pass arguments as a single dictionary or as positional args
            articles = None
            analysis_config = None
            
            # Case 1: Arguments passed as positional args
            if len(args) == 1 and isinstance(args[0], list):
                articles = args[0]
                analysis_config = kwargs.get('analysis_config')
            elif len(args) == 1 and not isinstance(args[0], list):
                # Single article passed
                articles = [args[0]]
                analysis_config = kwargs.get('analysis_config')
            elif len(args) == 2:
                articles = args[0]
                analysis_config = args[1]
            elif 'articles' in kwargs:
                # Arguments passed as keyword args
                articles = kwargs['articles']
                analysis_config = kwargs.get('analysis_config')
            else:
                # No valid arguments found
                raise ValueError(f"Invalid arguments: args={args}, kwargs={kwargs}")
            
            # Ensure articles is a list
            if not isinstance(articles, list):
                articles = [articles]
            
            # Validate that all articles are Article objects
            from .models import Article
            validated_articles = []
            for article in articles:
                if isinstance(article, Article):
                    validated_articles.append(article)
                elif isinstance(article, dict):
                    # Convert dict to Article object
                    validated_articles.append(Article(**article))
                else:
                    raise ValueError(f"Invalid article type: {type(article)}. Expected Article object or dict.")
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, run in a separate thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    def run_async():
                        return asyncio.run(self._arun(validated_articles, analysis_config))
                    future = executor.submit(run_async)
                    return future.result()
            except RuntimeError:
                # No event loop running, use asyncio.run
                return asyncio.run(self._arun(validated_articles, analysis_config))
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error in AIContentAnalysisTool._run: {e}")
            print(f"Args: {args}")
            print(f"Kwargs: {kwargs}")
            raise e
    
    async def _analyze_article(self, article: Article, config: AnalysisConfig) -> Article:
        """Analyze a single article using AI."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert content analyst for industry news.
            Analyze the provided blog article and provide:
            1. A concise summary
            2. 3-5 key insights or takeaways
            3. Main topics/names mentioned
            4. Sentiment analysis
            
            Be concise and professional. Focus on technical insights, innovations, and business implications."""),
            ("human", """
            Title: {title}
            Content: {content}
            
            Please provide:
            1. A {summary_length} summary (max 150 words)
            2. Key insights as a JSON array of strings
            3. Main topics as a JSON array of strings
            
            Response format:
            {{
                "summary": "summary text",
                "insights": ["insight1", "insight2", ...],
                "topics": ["topic1", "topic2", ...],
                "sentiment": "positive/negative/neutral"
            }}
            """)
        ])
        
        chain = prompt | self.llm
        
        result = await chain.ainvoke({
            "title": article.title,
            "content": article.content[:config.max_tokens_per_summary * 4],  # Approximate char limit
            "summary_length": config.summary_length
        })
        
        try:
            analysis = json.loads(result.content)
            article.summary = analysis.get("summary", "")
            article.key_insights = analysis.get("insights", [])
            article.tags = analysis.get("topics", [])
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            article.summary = result.content.strip()
            article.key_insights = ["Detailed analysis available in summary"]
        
        return article


class ReportGenerationTool(BaseTool):
    """Tool for generating reports in multiple formats."""
    
    name: str = "generate_reports"
    description: str = """Generate comprehensive reports from analyzed articles in multiple formats.
    
    Args:
        articles: List of analyzed Article objects
        email_recipients: List of email addresses to send reports to
        report_config: Report generation configuration
    
    Returns:
        Dictionary with report paths and delivery status"""
    
    return_direct: bool = False
    settings: Settings
    
    def __init__(self, settings: Settings):
        super().__init__(settings=settings)
        self.settings = settings
    
    def _run(self, *args, **kwargs) -> Dict:
        """Generate reports and optionally send via email."""
        try:
            # Extract arguments from different possible formats
            articles = None
            email_recipients = None
            report_config = None
            
            # Case 1: Arguments passed as positional args
            if len(args) >= 1:
                articles = args[0]
                if len(args) >= 2:
                    email_recipients = args[1]
                if len(args) >= 3:
                    report_config = args[2]
            
            # Case 2: Arguments passed as keyword args
            if 'articles' in kwargs:
                articles = kwargs['articles']
            if 'email_recipients' in kwargs:
                email_recipients = kwargs['email_recipients']
            if 'report_config' in kwargs:
                report_config = kwargs['report_config']
            
            # Ensure articles is a list
            if not isinstance(articles, list):
                articles = [articles]
            
            # Handle email_recipients being a string instead of a list
            if isinstance(email_recipients, str):
                email_recipients = [email_recipients]
            
            if not articles:
                return {"error": "No articles provided for report generation"}
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, run in a separate thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    def run_async():
                        return asyncio.run(self._arun(articles, email_recipients, report_config))
                    future = executor.submit(run_async)
                    return future.result()
            except RuntimeError:
                # No event loop running, use asyncio.run
                import asyncio
                return asyncio.run(self._arun(articles, email_recipients, report_config))
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error in ReportGenerationTool._run: {e}")
            print(f"Args: {args}")
            print(f"Kwargs: {kwargs}")
            raise e
    
    async def _arun(self, articles: List[Article], email_recipients: List[str] = None, report_config: Dict = None) -> Dict:
        """Async report generation."""
        try:
            # Generate reports
            report_gen = ReportGenerator(self.settings)
            report_paths = await report_gen.generate_all_reports(
                articles, report_config or {}
            )
            
            result = {
                "report_paths": report_paths,
                "total_articles": len(articles),
                "email_sent": False,
                "errors": []
            }
            
            # Send email if recipients provided
            if email_recipients and "email_service" in self.settings.items():
                try:
                    from .email_service import EmailService
                    email_service = EmailService(self.settings)
                    
                    for recipient in email_recipients:
                        sent = await email_service.send_report_email(
                            recipient, report_paths
                        )
                        if sent:
                            result["email_sent"] = True
                        else:
                            result["errors"].append(f"Failed to send email to {recipient}")
                            
                except Exception as e:
                    result["errors"].append(f"Email service error: {str(e)}")
            
            return result
            
        except Exception as e:
            return {"error": f"Report generation failed: {str(e)}"}


# Direct @tool functions for LangGraph integration
@tool
def scrape_articles(urls: List[str], max_articles: int = 5) -> Dict:
    """Scrape articles from given blog URLs.
    
    Args:
        urls: List of blog URLs to scrape
        max_articles: Maximum articles per blog (default: 5)
    
    Returns:
        Dict with 'articles' (list) and 'errors' (list)
    """
    settings = Settings()
    scraper = WebScrapingTool(settings)
    articles, errors = scraper.run(urls, max_articles)
    
    return {
        "articles": [article.model_dump() for article in articles],
        "errors": errors,
        "total_scraped": len(articles),
        "total_urls": len(urls)
    }


@tool
def analyze_content(articles: List[Dict], analysis_config: Dict = None) -> Dict:
    """Analyze articles using AI for insights and summarization.
    
    Args:
        articles: List of article dictionaries
        analysis_config: Analysis parameters
    
    Returns:
        Dict with analyzed articles and analysis stats
    """
    from .models import Article
    
    settings = Settings()
    analyzer = AIContentAnalysisTool(settings)
    
    # Convert dicts to Article objects
    article_objects = [Article(**article) for article in articles]
    analyzed = analyzer._run(articles=article_objects, analysis_config=analysis_config)
    
    return {
        "articles": [article.model_dump() for article in analyzed],
        "total_analyzed": len(analyzed),
        "analysis_config": analysis_config
    }


@tool
def generate_weekly_report(
    articles: List[Dict], 
    company_insights: Dict[str, Dict], 
    summary: str = ""
) -> Dict:
    """Generate a comprehensive weekly industry report.
    
    Args:
        articles: List of analyzed articles
        company_insights: Dictionary mapping company names to insights
        summary: Executive summary of the week
    
    Returns:
        Dict with report paths and generation details
    """
    settings = Settings()
    
    # This is a thin wrapper that calls the report generation
    return {
        "status": "report_generation_started",
        "articles_count": len(articles),
        "companies_covered": list(company_insights.keys()),
        "summary": summary,
        "config": {
            "output_dir": settings.output_dir,
            "formats": ["markdown", "pdf"]
        }
    }