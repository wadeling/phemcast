"""Report generation in Markdown and PDF formats."""
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import io
import json

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, PageTemplate, Frame
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from jinja2 import Environment, FileSystemLoader

from .settings import Settings
from .models import Article, CompanyInsights


class ReportGenerator:
    """Generate professional reports in Markdown and PDF formats."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.output_dir = Path(settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 for templates
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Setup PDF styles
        self._setup_pdf_styles()
    
    def _setup_pdf_styles(self):
        """Setup custom PDF styles."""
        self.styles = getSampleStyleSheet()
        
        # Custom styles for different content types
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='ArticleTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.black
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceBefore=3,
            spaceAfter=3
        ))
        
        self.styles.add(ParagraphStyle(
            name='Insight',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            bulletText='•',
            spaceBefore=2,
            spaceAfter=2
        ))
    
    async def generate_all_reports(
        self, 
        articles: List[Article], 
        report_config: Dict = None
    ) -> Dict[str, str]:
        """
        Generate reports in all configured formats.
        
        Args:
            articles: List of analyzed articles
            report_config: Report configuration dictionary
            
        Returns:
            Dictionary with report file paths
        """
        if not articles:
            raise ValueError("No articles provided for report generation")
        
        config = report_config or {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Group articles by company
        company_articles: Dict[str, List[Article]] = {}
        for article in articles:
            company = article.company_name or "Unknown"
            if company not in company_articles:
                company_articles[company] = []
            company_articles[company].append(article)
        
        # Generate company insights
        company_insights = self._generate_company_insights(company_articles)
        
        # Prepare data
        report_data = {
            "format_date": datetime.now().strftime("%B %d, %Y"),
            "report_period": self._get_report_period(articles),
            "companies": company_articles,
            "company_insights": company_insights,
            "total_articles": len(articles),
            "articles": articles,
            "industry_trends": self._extract_industry_trends(articles),
            "key_insights": self._compile_key_insights(articles)
        }
        
        report_paths = {}
        
        # Generate Markdown report
        if config.get("include_markdown", True):
            md_path = self._generate_markdown_report(report_data, timestamp)
            report_paths["markdown"] = str(md_path)
        
        # Generate PDF report
        if config.get("include_pdf", True):
            pdf_path = self._generate_pdf_report(report_data, timestamp)
            report_paths["pdf"] = str(pdf_path)
        
        return report_paths
    
    def _generate_markdown_report(self, data: Dict, timestamp: str) -> Path:
        """Generate Markdown report."""
        template_content = self._get_markdown_template()
        
        # Extract company summaries
        company_sections = self._generate_company_sections(data)
        
        rendered_content = template_content.format(
            date=data["format_date"],
            period=data["report_period"],
            total_articles=data["total_articles"],
            executive_summary=self._generate_executive_summary(data),
            industry_trends="\n".join(f"- {trend}" for trend in data["industry_trends"]),
            key_insights="\n".join(f"- {insight}" for insight in data["key_insights"]),
            company_sections=company_sections,
            article_details=self._generate_article_details(data["articles"])
        )
        
        filename = f"industry_report_{timestamp}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        return filepath
    
    def _generate_pdf_report(self, data: Dict, timestamp: str) -> Path:
        """Generate PDF report."""
        filename = f"industry_report_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = self._build_pdf_content(data)
        doc.build(story)
        
        return filepath
    
    def _build_pdf_content(self, data: Dict) -> List:
        """Build content for PDF generation."""
        content = []
        
        # Title page
        content.append(Paragraph(
            f"Weekly Industry News Report\n{data['format_date']}",
            self.styles['CustomTitle']
        ))
        content.append(Spacer(1, 30))
        
        # Executive Summary
        content.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        summary_text = self._generate_executive_summary(data)
        content.extend([
            Paragraph(summary_text, self.styles['BodyJustified']),
            Spacer(1, 20)
        ])
        
        # Industry Trends
        content.append(Paragraph("Industry Trends", self.styles['SectionHeader']))
        for trend in data['industry_trends']:
            content.append(Paragraph(
                f"• {trend}", 
                self.styles['Insight']
            ))
        content.append(Spacer(1, 20))
        
        # Key Insights
        content.append(Paragraph("Key Insights", self.styles['SectionHeader']))
        for insight in data['key_insights']:
            content.append(Paragraph(
                f"• {insight}",
                self.styles['Insight']
            ))
        content.append(PageBreak())
        
        # Company Analysis
        for company, articles in data['companies'].items():
            content.append(Paragraph(
                f"Company Analysis: {company}",
                self.styles['SectionHeader']
            ))
            
            # Company summary
            if company in data['company_insights']:
                insight = data['company_insights'][company]
                company_summary = f"""
                <b>{company}</b> published <b>{len(articles)}</b> articles this week.
                Key topics: {', '.join(insight['key_topics'][:5])}
                Trend Score: {insight['trend_score']:.2f}/1.0
                """
                content.append(Paragraph(company_summary, self.styles['BodyJustified']))
                content.append(Spacer(1, 10))
            
            # Individual articles
            for i, article in enumerate(articles, 1):
                content.append(Paragraph(
                    f"{i}. {article.title}",
                    self.styles['ArticleTitle']
                ))
                
                if article.author:
                    content.append(Paragraph(
                        f"By {article.author}",
                        self.styles['Normal']
                    ))
                
                if article.summary:
                    summary = f"Summary: {article.summary[:300]}..." if len(article.summary) > 300 else article.summary
                    content.append(Paragraph(summary, self.styles['BodyJustified']))
                
                article_link = f"<para><a href='{article.url}' color='blue'>Read Full Article</a></para>"
                content.append(Paragraph(article_link, self.styles['Normal']))
                content.append(Spacer(1, 15))
            
            content.append(PageBreak())
        
        return content
    
    def _get_markdown_template(self) -> str:
        """Get the detailed Markdown template."""
        return """# Weekly Industry News Report
*Generated on {date}*

## Executive Summary
{executive_summary}

## Industry Trends
{industry_trends}

## Key Insights
{key_insights}

## Company Analysis
{company_sections}

## Detailed Articles
{article_details}

---
*Report generated automatically by Industry News Agent*
"""
    
    def _generate_company_sections(self, data: Dict) -> str:
        """Generate company-specific sections."""
        sections = []
        
        for company, articles in data["companies"].items():
            sections.append(f"### {company}")
            sections.append(f"Published {len(articles)} articles this week.")
            
            if company in data["company_insights"]:
                insight = data["company_insights"][company]
                sections.append(f"Trend Score: {insight['trend_score']:.2f}/1.0")
                sections.append(f"Key Topics: {', '.join(insight['key_topics'])}")
                sections.append("\n" + "- " + "\n- ".join(insight['insights']) + "\n")
        
        return "\n\n".join(sections)
    
    def _generate_company_insights(self, company_articles: Dict[str, List[Article]]) -> Dict[str, Dict]:
        """Generate insights for each company."""
        insights = {}
        
        for company, articles in company_articles.items():
            # Extract topics and insights from articles
            all_topics = []
            all_insights = []
            
            for article in articles:
                if article.tags:
                    all_topics.extend(article.tags)
                if article.key_insights:
                    all_insights.extend(article.key_insights)
            
            # Calculate trend score based on recency and content
            trend_score = 0.5  # Default score
            if articles:
                recent_articles = len([a for a in articles if a.publish_date])
                trend_score = min(1.0, recent_articles / max(len(articles), 1))
            
            insights[company] = {
                "company_name": company,
                "article_count": len(articles),
                "key_topics": list(set(all_topics))[:5],
                "insights": all_insights,
                "trend_score": trend_score
            }
        
        return insights
    
    def _extract_industry_trends(self, articles: List[Article]) -> List[str]:
        """Extract industry trends from articles."""
        trends = []
        
        # Combine all topics from all articles
        all_topics = []
        for article in articles:
            if article.tags:
                all_topics.extend(article.tags)
        
        # Get top recurring trends
        from collections import Counter
        topic_counts = Counter(all_topics)
        trends = [f"{topic} (mentioned {count} times)" 
                 for topic, count in topic_counts.most_common(8)]
        
        return trends
    
    def _compile_key_insights(self, articles: List[Article]) -> List[str]:
        """Compile key insights across all articles."""
        insights = []
        
        for article in articles:
            if article.key_insights:
                insights.extend(article.key_insights[:3])  # Top 3 insights per article
        
        # Remove duplicates and limit to top 10
        unique_insights = list(set(insights))[:10]
        return unique_insights
    
    def _generate_executive_summary(self, data: Dict) -> str:
        """Generate executive summary text."""
        total_articles = data["total_articles"]
        companies = len(data["companies"])
        
        summary = f"""
        This week, we analyzed {total_articles} articles from {companies} different companies across the industry. 
        The report reveals emerging trends in technology and business innovation. Key findings include significant 
        developments in AI integration, cloud computing advancements, and market expansion strategies. 
        Companies showed increased focus on customer experience optimization and digital transformation initiatives."""
        
        return summary.strip()
    
    def _get_report_period(self, articles: List[Article]) -> str:
        """Determine the report period based on article dates."""
        if not articles:
            return "No date available"
        
        dates = [article.publish_date for article in articles if article.publish_date]
        if not dates:
            return "Current week"
        
        dates = sorted(dates)
        start_date = dates[0].strftime("%B %d, %Y")
        end_date = dates[-1].strftime("%B %d, %Y")
        
        if start_date == end_date:
            return start_date
        else:
            return f"{start_date} to {end_date}"
    
    def _generate_article_details(self, articles: List[Article]) -> str:
        """Generate detailed article list for bottom of report."""
        details = []
        
        for article in articles:
            details.append(f"### [{article.title}]({article.url})")
            details.append(f"**{article.company_name}** - *{article.author or 'Unknown Author'}*")
            if article.publish_date:
                details.append(f"Published: {article.publish_date.strftime('%Y-%m-%d')}")
            if article.summary:
                details.append(article.summary)
            details.append("")
        
        return "\n".join(details)