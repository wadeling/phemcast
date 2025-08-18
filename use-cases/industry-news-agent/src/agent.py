"""LangGraph agent for industry news aggregation and analysis."""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from .settings import Settings, load_settings
from .models import AgentState, Article, CompanyInsights
from .tools import scrape_articles, analyze_content, generate_weekly_report
from .web_scraper import AsyncWebScraper
from .report_generator import ReportGenerator
from .email_service import EmailService


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
        workflow.add_node("generate_aggregation", self._generate_aggregation)
        workflow.add_node("generate_reports", self._generate_reports)
        workflow.add_node("send_emails", self._send_emails)
        
        # Add edges (workflow flow)
        workflow.set_entry_point("validate_urls")
        workflow.add_edge("validate_urls", "scrape_articles")
        workflow.add_edge("scrape_articles", "analyze_content")
        workflow.add_edge("analyze_content", "generate_aggregation")
        workflow.add_edge("generate_aggregation", "generate_reports")
        workflow.add_edge("generate_reports", "send_emails")
        workflow.add_edge("send_emails", END)
        
        # Compile workflow
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)
    
    async def run_workflow(
        self, 
        urls: List[str], 
        email_recipients: List[str] = None, 
        max_articles: int = 5
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
                "urls": urls,
                "email_recipients": email_recipients or [],
                "max_articles": max_articles,
                "processing_status": "starting",
                "errors": [],
                "total_tokens_used": 0,
                "progress": {"total": len(urls), "completed": 0},
                "logs": ["🎯 Starting report generation for {} URLs".format(len(urls))],
                "total_urls": len(urls),
                "total_articles": 0
            }
            
            logger.info(f"Starting workflow with {len(urls)} URLs, max_articles: {max_articles}")
            
            # Run the workflow without checkpointing for background processing
            config = {"configurable": {"thread_id": f"background_{datetime.now().timestamp()}"}}
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            return {
                "status": final_state.get("processing_status", "completed"),
                "errors": final_state.get("errors", []),
                "total_articles": len(final_state.get("articles", [])),
                "total_urls": final_state.get("total_urls", 0),
                "report_paths": {
                    "markdown": final_state.get("report_path_md", ""),
                    "pdf": final_state.get("report_path_pdf", "")
                },
                "email_sent": final_state.get("email_sent", False),
                "total_tokens_used": final_state.get("total_tokens_used", 0),
                "logs": final_state.get("logs", []),
                "processing_time": final_state.get("processing_time", 0)
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
    
    async def _scrape_articles(self, state: AgentState) -> AgentState:
        """Scrape articles from validated URLs."""
        urls = state.get("urls", [])
        max_articles = state.get("max_articles", 5)
        logger.debug(f"Scraping articles from {len(urls)} URLs, max_articles: {max_articles}")
        
        try:
            async with AsyncWebScraper(self.settings) as scraper:
                articles, scrape_errors = await scraper.scrape_blog_articles(
                    urls, max_articles
                )
            
            # Convert scraped data to Article objects if needed
            article_objects = []
            if articles and isinstance(articles[0], dict):
                from .models import Article
                article_objects = [Article(**article) for article in articles]
            else:
                article_objects = articles
            
            state.update({
                "articles": article_objects,
                "processing_status": "articles_scraped",
                "errors": state.get("errors", []) + scrape_errors,
                "progress": {"total": len(urls), "completed": len(urls)},
                "logs": state.get("logs", []) + [
                    f"✅ Scraped {len(article_objects)} articles from {len(urls)} URLs",
                    f"📈 URL processing: 100% complete"
                ],
                "total_articles": len(article_objects)
            })
            
            logger.info(f"Scraped {len(article_objects)} articles from {len(urls)} URLs")
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
            from .tools import AIContentAnalysisTool
            
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
    
    async def _generate_aggregation(self, state: AgentState) -> AgentState:
        """Generate company insights and industry aggregation."""
        articles = state.get("articles", [])
        
        if not articles:
            state["company_insights"] = {}
            state["processing_status"] = "aggregation_complete"
            return state
        
        # Group articles by company
        company_articles: Dict[str, List[Article]] = {}
        for article in articles:
            company = article.company_name or "Unknown Company"
            if company not in company_articles:
                company_articles[company] = []
            company_articles[company].append(article)
        
        # Generate insights
        company_insights: Dict[str, CompanyInsights] = {}
        
        for company, company_arts in company_articles.items():
            all_topics = []
            all_insights = []
            
            for article in company_arts:
                all_topics.extend(article.tags or [])
                all_insights.extend(article.key_insights or [])
            
            # Calculate trend score
            trend_score = min(1.0, len(company_arts) / 5)  # Simple scoring
            
            # Extract domain from first article's URL
            domain = "unknown"
            if company_arts and company_arts[0].url:
                from urllib.parse import urlparse
                parsed = urlparse(company_arts[0].url)
                domain = parsed.netloc
            
            insight = CompanyInsights(
                company_name=company,
                domain=domain,
                article_count=len(company_arts),
                insights=list(set(all_insights)),
                trend_score=trend_score,
                key_topics=list(set(all_topics))[:5]
            )
            
            company_insights[company] = insight
        
        state.update({
            "company_insights": company_insights,
            "processing_status": "aggregation_complete"
        })
        
        logger.info(f"Generated insights for {len(company_insights)} companies")
        return state
    
    async def _generate_reports(self, state: AgentState) -> AgentState:
        """Generate final reports."""
        articles = state.get("articles", [])
        company_insights = state.get("company_insights", {})
        
        logger.info(f"Starting report generation with {len(articles)} articles and {len(company_insights)} company insights")
        
        if not articles:
            logger.warning("No articles available for report generation")
            state["report_path_md"] = ""
            state["report_path_pdf"] = ""
            state["processing_status"] = "reports_generated"
            return state
        
        try:
            start_time = datetime.now()
            total_articles = len(articles)
            
            state["logs"] = state.get("logs", []) + [f"📝 Starting report generation for {total_articles} articles"]
            
            report_generator = ReportGenerator(self.settings)
            
            # Add execution metadata
            report_metadata = {
                "total_articles": total_articles,
                "companies": list(company_insights.keys()),
                "execution_date": datetime.now()
            }
            
            logger.info(f"Calling ReportGenerator.generate_all_reports with {len(articles)} articles")
            report_paths = await report_generator.generate_all_reports(
                articles, {}
            )
            
            logger.info(f"ReportGenerator returned paths: {report_paths}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            state.update({
                "report_path_md": report_paths.get("markdown", ""),
                "report_path_pdf": report_paths.get("pdf", ""),
                "processing_status": "reports_generated",
                "logs": state.get("logs", []) + [
                    f"✅ Reports generated: {list(report_paths.keys())}",
                    f"⏱️ Report generation time: {processing_time:.1f}s"
                ],
                "processing_time": processing_time
            })
            
            logger.info(f"Generated reports: {list(report_paths.keys())}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            state.update({
                "processing_status": "error",
                "errors": state.get("errors", []) + [f"Report generation failed: {str(e)}"],
                "logs": state.get("logs", []) + [f"❌ Report generation failed: {str(e)}"]
            })
        
        return state
    
    async def _send_emails(self, state: AgentState) -> AgentState:
        """Send reports via email."""
        report_path_md = state.get("report_path_md", "")
        report_path_pdf = state.get("report_path_pdf", "")
        recipients = state.get("email_recipients", [])
        
        # Create report_paths dict for compatibility with email service
        report_paths = {}
        if report_path_md:
            report_paths["markdown"] = report_path_md
        if report_path_pdf:
            report_paths["pdf"] = report_path_pdf
        
        # Add more detailed logging
        logger.info(f"=== EMAIL SENDING STEP ===")
        logger.info(f"State keys: {list(state.keys())}")
        logger.info(f"Processing status: {state.get('processing_status')}")
        logger.info(f"Articles count: {len(state.get('articles', []))}")
        logger.info(f"Company insights count: {len(state.get('company_insights', {}))}")
        logger.info(f"Ready to send emails to recipients: {recipients}")
        logger.info(f"Report path MD: {report_path_md}")
        logger.info(f"Report path PDF: {report_path_pdf}")
        logger.info(f"Report paths dict: {report_paths}")
        logger.info(f"Report paths empty: {not report_paths}")

        if not recipients:
            state["email_sent"] = False
            state["processing_status"] = "completed"
            state["logs"] = state.get("logs", []) + ["📧 No email recipients specified - skipping email delivery"]
            return state
        
        if not report_paths:
            state.update({
                "processing_status": "error",
                "errors": state.get("errors", []) + ["No reports to send"],
                "logs": state.get("logs", []) + ["❌ Cannot send email - no reports generated"]
            })
            return state
        
        try:
            state["logs"] = state.get("logs", []) + [f"📧 Starting email delivery to {len(recipients)} recipients"]
            
            # Prepare metadata for email content
            articles = state.get("articles", [])
            company_insights = state.get("company_insights", {})
            report_metadata = {
                "total_articles": len(articles),
                "companies": list(company_insights.keys()),
                "execution_date": datetime.now()
            }
            
            logger.info(f"Email metadata: {report_metadata}")
            
            email_service = EmailService(self.settings)
            
            email_results = await email_service.send_bulk_reports(
                recipients, report_paths, report_metadata
            )
            
            # Check if at least one email was sent successfully
            any_sent = any(email_results.values())
            success_count = list(email_results.values()).count(True)
            
            state.update({
                "email_sent": any_sent,
                "email_results": email_results,
                "processing_status": "completed",
                "logs": state.get("logs", []) + [
                    f"📧 Email sending complete: {success_count}/{len(recipients)} succeeded",
                    f"✅ Report processing completed successfully!"
                ]
            })
            
            if not any_sent:
                state["errors"] = state.get("errors", []) + ["All email deliveries failed"]
            
            logger.info(f"Email sending completed: {email_results}")
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            state.update({
                "processing_status": "error",
                "errors": state.get("errors", []) + [f"Email sending failed: {str(e)}"],
                "logs": state.get("logs", []) + [f"❌ Email sending failed: {str(e)}"]
            })
        
        return state


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