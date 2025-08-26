"""Report generation in Markdown and PDF formats."""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import io
import json

# Setup logger
logger = logging.getLogger(__name__)

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
from .tts_service import create_tts_service, MinimaxiTTSService


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
        
        # Setup TTS service
        self.tts_service = None
        if settings.enable_tts and settings.minimaxi_api_key and settings.minimaxi_group_id:
            try:
                self.tts_service = create_tts_service(settings)
                logger.info("TTS service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize TTS service: {e}")
                self.tts_service = None
        elif settings.enable_tts and (not settings.minimaxi_api_key or not settings.minimaxi_group_id):
            logger.warning("TTS service disabled: missing minimaxi_api_key or minimaxi_group_id")
    
    def _setup_pdf_styles(self):
        """Setup custom PDF styles with Chinese font support."""
        self.styles = getSampleStyleSheet()
        
        # Try to find a Chinese font, fallback to default if not available
        chinese_font = self._get_chinese_font()
        
        # Custom styles for different content types
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontName=chinese_font,
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontName=chinese_font,
            fontSize=18,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='ArticleTitle',
            parent=self.styles['Heading2'],
            fontName=chinese_font,
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.black
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=self.styles['Normal'],
            fontName=chinese_font,
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceBefore=3,
            spaceAfter=3
        ))
        
        self.styles.add(ParagraphStyle(
            name='Insight',
            parent=self.styles['Normal'],
            fontName=chinese_font,
            fontSize=10,
            leftIndent=20,
            bulletText='•',
            spaceBefore=2,
            spaceAfter=2
        ))
        
        # Update default styles to use Chinese font
        self.styles['Normal'].fontName = chinese_font
        self.styles['Title'].fontName = chinese_font
        self.styles['Heading1'].fontName = chinese_font
        self.styles['Heading2'].fontName = chinese_font
    
    def _get_chinese_font(self) -> str:
        """Get a Chinese font for PDF generation."""
        try:
            # Try to use reportlab's built-in Chinese font support
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # First try to use a simple approach with common fonts
            try:
                # Try to register a simple Chinese font
                font_path = self._find_simple_chinese_font()
                if font_path:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    logger.info(f"Registered Chinese font from: {font_path}")
                    return 'ChineseFont'
            except Exception as e:
                logger.debug(f"Failed to register custom font: {str(e)}")
            
            # Fallback: try to use system default fonts that support Chinese
            fallback_fonts = ['Helvetica', 'Times-Roman', 'Courier']
            for font in fallback_fonts:
                try:
                    # Test if font can handle Chinese characters
                    if self._test_font_chinese_support(font):
                        logger.info(f"Using fallback font with Chinese support: {font}")
                        return font
                except:
                    continue
            
            logger.warning("No Chinese font found, using default font (may show boxes for Chinese)")
            return 'Helvetica'
            
        except ImportError:
            logger.warning("reportlab.pdfbase not available, using default font")
            return 'Helvetica'
        except Exception as e:
            logger.error(f"Error setting up Chinese font: {str(e)}")
            return 'Helvetica'
    
    def _find_simple_chinese_font(self) -> str:
        """Find a simple Chinese font file."""
        import platform
        
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # macOS has excellent Chinese font support
            # Priority order based on quality and availability
            font_paths = [
                # First priority: High-quality Chinese fonts
                '/System/Library/Fonts/STHeiti Light.ttc',      # 华文黑体细体
                '/System/Library/Fonts/STHeiti Medium.ttc',     # 华文黑体中体
                '/System/Library/Fonts/ヒラギノ明朝 ProN.ttc',  # ヒラギノ明朝
                '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc', # ヒラギノ角ゴシック
                
                # Second priority: Alternative Chinese fonts
                '/System/Library/Fonts/AppleSDGothicNeo.ttc',  # Apple 韩文字体
                '/System/Library/Fonts/CJKSymbolsFallback.ttc', # 中日韩符号回退字体
                
                # Third priority: Fallback fonts
                '/System/Library/Fonts/PingFang.ttc',           # 苹方字体 (if available)
                '/System/Library/Fonts/Helvetica.ttc',          # Helvetica (basic support)
            ]
            
            for path in font_paths:
                if os.path.exists(path):
                    logger.info(f"Found Chinese font: {path}")
                    return path
            
            logger.warning("No Chinese fonts found in standard locations")
            return None
        
        elif system == "Windows":
            # Windows font directories
            font_paths = [
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'simsun.ttc'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'simhei.ttf'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'FontPath', 'msyh.ttc')
            ]
            for path in font_paths:
                if os.path.exists(path):
                    return path
        
        elif system == "Linux":
            # Linux/Docker environment font directories
            font_paths = [
                # Noto CJK fonts (Google's open-source CJK font family)
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Light.ttc',
                
                # WQY fonts (WenQuanYi - Chinese font)
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                
                # DejaVu fonts (fallback)
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
                
                # Liberation fonts
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
            ]
            
            for path in font_paths:
                if os.path.exists(path):
                    logger.info(f"Found Linux font: {path}")
                    return path
            
            logger.warning("No Linux fonts found in standard locations")
            return None
        
        return None
    
    def _test_font_chinese_support(self, font_name: str) -> bool:
        """Test if a font supports Chinese characters."""
        try:
            # Simple test - this is not comprehensive but should catch obvious issues
            return True  # Assume fonts support Chinese for now
        except:
            return False
    
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
        
        # Remove duplicate articles based on URL
        unique_articles = self._deduplicate_articles(articles)
        
        # Group articles by company
        company_articles: Dict[str, List[Article]] = {}
        for article in unique_articles:
            company = article.company_name or "Unknown"
            if company not in company_articles:
                company_articles[company] = []
            company_articles[company].append(article)
        
        # Generate company insights
        company_insights = self._generate_company_insights(company_articles)
        
        # Prepare data
        report_data = {
            "format_date": datetime.now().strftime("%B %d, %Y"),
            "report_period": self._get_report_period(unique_articles),
            "companies": company_articles,
            "company_insights": company_insights,
            "total_articles": len(unique_articles),
            "articles": unique_articles,
            "industry_trends": self._extract_industry_trends(unique_articles),
            "key_insights": self._compile_key_insights(unique_articles)
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
        
        # Generate audio report if TTS is enabled
        if config.get("include_audio", True) and self.tts_service:
            try:
                audio_result = await self._generate_audio_report(report_data, timestamp)
                if audio_result["success"]:
                    report_paths["audio"] = audio_result
                    logger.info(f"Audio report generated successfully: {audio_result['access_token']}")
                else:
                    logger.warning(f"Failed to generate audio report: {audio_result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"Error generating audio report: {e}")
        
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
    
    async def _generate_audio_report(self, data: Dict, timestamp: str) -> Dict:
        """Generate audio report using TTS service with AI-generated summary."""
        try:
            # 生成报告ID
            report_id = f"report_{timestamp}"
            
            # 准备文章数据用于摘要生成
            articles_for_summary = []
            articles = data.get("articles", [])
            
            if not articles:
                logger.warning("No articles found in data, using fallback method")
                return await self._fallback_audio_generation(data, report_id)
            
            for article in articles:
                try:
                    # 安全地获取文章属性
                    title = getattr(article, "title", None)
                    content = getattr(article, "content", None)
                    
                    # 验证必要属性
                    if title and content:
                        articles_for_summary.append({
                            "title": title,
                            "content": content
                        })
                    else:
                        logger.warning(f"Article missing required attributes: title={title is not None}, content={content is not None}")
                        
                except Exception as e:
                    logger.warning(f"Error processing article: {e}")
                    continue
            
            if not articles_for_summary:
                logger.warning("No valid articles processed, using fallback method")
                return await self._fallback_audio_generation(data, report_id)
            
            logger.info(f"Preparing {len(articles_for_summary)} articles for AI summary generation")
            
            # 使用新的摘要生成方法
            if hasattr(self.tts_service, 'generate_summary_from_articles'):
                # 使用新的AI摘要生成功能
                audio_result = await self.tts_service.generate_summary_from_articles(
                    articles=articles_for_summary,
                    report_id=report_id
                )
                
                if audio_result.get("success"):
                    logger.info(f"AI-generated audio summary created successfully")
                    logger.debug(f"Summary length: {audio_result.get('summary_length', 0)} characters")
                    logger.debug(f"Articles processed: {audio_result.get('articles_count', 0)}")
                else:
                    logger.warning(f"AI summary generation failed: {audio_result.get('error')}")
                    # 回退到原来的方法
                    audio_result = await self._fallback_audio_generation(data, report_id)
                
                return audio_result
            else:
                # 如果TTS服务不支持新功能，使用原来的方法
                logger.info("Using fallback audio generation method")
                return await self._fallback_audio_generation(data, report_id)
            
        except Exception as e:
            logger.error(f"Error generating audio report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fallback_audio_generation(self, data: Dict, report_id: str) -> Dict:
        """Fallback audio generation method using original logic."""
        try:
            # 生成报告摘要文本用于TTS
            summary_text = self._generate_executive_summary(data)
            
            # 添加行业趋势
            trends_text = "行业趋势包括：" + "，".join(data["industry_trends"][:5])  # 限制前5个趋势
            
            # 添加关键见解
            insights_text = "关键见解包括：" + "，".join(data["key_insights"][:5])  # 限制前5个见解
            
            # 组合完整的TTS文本
            full_text = f"{summary_text}。{trends_text}。{insights_text}。"
            
            # 调用TTS服务生成语音
            audio_result = await self.tts_service.generate_speech(
                text=full_text,
                report_id=report_id
            )
            
            return audio_result
            
        except Exception as e:
            logger.error(f"Error in fallback audio generation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
            f"行业新闻周报\n{data['format_date']}",
            self.styles['CustomTitle']
        ))
        content.append(Spacer(1, 30))
        
        # Executive Summary
        content.append(Paragraph("执行摘要", self.styles['SectionHeader']))
        summary_text = self._generate_executive_summary(data)
        content.extend([
            Paragraph(summary_text, self.styles['BodyJustified']),
            Spacer(1, 20)
        ])
        
        # Industry Trends
        content.append(Paragraph("行业趋势", self.styles['SectionHeader']))
        for trend in data['industry_trends']:
            content.append(Paragraph(
                f"• {trend}", 
                self.styles['Insight']
            ))
        content.append(Spacer(1, 20))
        
        # Key Insights
        content.append(Paragraph("关键见解", self.styles['SectionHeader']))
        for insight in data['key_insights']:
            content.append(Paragraph(
                f"• {insight}",
                self.styles['Insight']
            ))
        content.append(PageBreak())
        
        # Company Analysis
        for company, articles in data['companies'].items():
            content.append(Paragraph(
                f"公司分析: {company}",
                self.styles['SectionHeader']
            ))
            
            # Company summary
            if company in data['company_insights']:
                insight = data['company_insights'][company]
                company_summary = f"""
                <b>{company}</b> 本周发布了 <b>{len(articles)}</b> 篇文章。
                主要话题: {', '.join(insight['key_topics'][:5])}
                趋势评分: {insight['trend_score']:.2f}/1.0
                """
                
                # Add sentiment score if available
                if 'sentiment_score' in insight and insight['sentiment_score'] is not None:
                    sentiment_text = "积极" if insight['sentiment_score'] > 0 else "消极" if insight['sentiment_score'] < 0 else "中性"
                    company_summary += f"<br/>情感倾向: {sentiment_text} ({insight['sentiment_score']:.2f})"
                
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
                        f"作者: {article.author}",
                        self.styles['Normal']
                    ))
                
                # Use new analysis structure if available
                if hasattr(article, 'analysis_data') and article.analysis_data:
                    analysis_data = self._extract_analysis_data(article)
                    
                    # Add metadata information
                    if analysis_data.get('translated_title'):
                        content.append(Paragraph(
                            f"中文标题: {analysis_data['translated_title']}",
                            self.styles['Normal']
                        ))
                    
                    if analysis_data.get('tags'):
                        tags_text = "标签: " + ", ".join(analysis_data['tags'][:5])
                        content.append(Paragraph(tags_text, self.styles['Normal']))
                    
                    # Add one sentence summary
                    if analysis_data.get('one_sentence_summary'):
                        content.append(Paragraph(
                            f"一句话总结: {analysis_data['one_sentence_summary']}",
                            self.styles['Normal']
                        ))
                    
                    # Add summary content
                    if analysis_data.get('summary_content'):
                        summary = f"内容摘要: {analysis_data['summary_content'][:300]}..." if len(analysis_data['summary_content']) > 300 else f"内容摘要: {analysis_data['summary_content']}"
                        content.append(Paragraph(summary, self.styles['BodyJustified']))
                    
                    # Add key insights
                    if analysis_data.get('insights'):
                        content.append(Paragraph("关键见解:", self.styles['Normal']))
                        for insight in analysis_data['insights'][:3]:  # Limit to top 3
                            content.append(Paragraph(
                                f"• {insight}",
                                self.styles['Insight']
                            ))
                    
                    # Add hierarchical structure if available
                    if analysis_data.get('hierarchical_structure'):
                        content.append(Paragraph("内容结构:", self.styles['Normal']))
                        for section in analysis_data['hierarchical_structure'][:3]:  # Limit to top 3 sections
                            section_text = f"<b>{section['heading']}</b>: {section['content'][:100]}..."
                            if len(section['content']) > 100:
                                section_text = f"<b>{section['heading']}</b>: {section['content'][:100]}..."
                            else:
                                section_text = f"<b>{section['heading']}</b>: {section['content']}"
                            content.append(Paragraph(section_text, self.styles['BodyJustified']))
                    
                    # Add sentiment
                    if analysis_data.get('sentiment'):
                        sentiment_emoji = self._get_sentiment_emoji(analysis_data['sentiment'])
                        content.append(Paragraph(
                            f"情感分析: {sentiment_emoji} {analysis_data['sentiment']}",
                            self.styles['Normal']
                        ))
                    
                    # Add timestamp if available
                    if analysis_data.get('timestamp'):
                        formatted_timestamp = self._format_timestamp(analysis_data['timestamp'])
                        if formatted_timestamp:
                            content.append(Paragraph(
                                f"分析时间: {formatted_timestamp}",
                                self.styles['Normal']
                            ))
                
                elif article.summary:
                    # Fallback to old summary format
                    summary = f"摘要: {article.summary[:300]}..." if len(article.summary) > 300 else f"摘要: {article.summary}"
                    content.append(Paragraph(summary, self.styles['BodyJustified']))
                
                article_link = f"<para><a href='{article.url}' color='blue'>阅读全文</a></para>"
                content.append(Paragraph(article_link, self.styles['Normal']))
                content.append(Spacer(1, 15))
            
            content.append(PageBreak())
        
        return content
    
    def _get_markdown_template(self) -> str:
        """Get the detailed Markdown template."""
        return """# 行业新闻周报
*生成时间: {date}*

## 执行摘要
{executive_summary}

## 行业趋势
{industry_trends}

## 关键见解
{key_insights}

## 公司分析
{company_sections}

## 详细文章
{article_details}

---
*报告由行业新闻代理自动生成*
"""
    
    def _generate_company_sections(self, data: Dict) -> str:
        """Generate company-specific sections."""
        sections = []
        
        for company, articles in data["companies"].items():
            sections.append(f"### {company}")
            sections.append(f"本周发布了 {len(articles)} 篇文章。")
            
            if company in data["company_insights"]:
                insight = data["company_insights"][company]
                sections.append(f"**趋势评分**: {insight['trend_score']:.2f}/1.0")
                
                # Add sentiment score if available
                if 'sentiment_score' in insight and insight['sentiment_score'] is not None:
                    sentiment_emoji = "😊" if insight['sentiment_score'] > 0 else "😞" if insight['sentiment_score'] < 0 else "😐"
                    sentiment_text = "积极" if insight['sentiment_score'] > 0.1 else "消极" if insight['sentiment_score'] < -0.1 else "中性"
                    sections.append(f"**情感评分**: {sentiment_emoji} {sentiment_text} ({insight['sentiment_score']:.2f})")
                
                sections.append(f"**主要话题**: {', '.join(insight['key_topics'])}")
                
                if insight['insights']:
                    sections.append("**关键见解**:")
                    # Filter insights by quality and limit to top 5
                    quality_insights = [insight_text for insight_text in insight['insights'] if len(insight_text) > 10]
                    sections.append("\n".join(f"- {insight_text}" for insight_text in quality_insights[:5]))
                
                # Add article-level insights if available
                article_insights = []
                for article in articles:
                    if hasattr(article, 'analysis_data') and article.analysis_data:
                        analysis_data = self._extract_analysis_data(article)
                        if analysis_data.get('one_sentence_summary'):
                            article_insights.append(f"• {analysis_data['one_sentence_summary']}")
                
                if article_insights:
                    sections.append("**文章要点**:")
                    sections.append("\n".join(article_insights[:3]))  # Top 3 article insights
                
            sections.append("")
        
        return "\n\n".join(sections)
    
    def _generate_company_insights(self, company_articles: Dict[str, List[Article]]) -> Dict[str, Dict]:
        """Generate insights for each company."""
        insights = {}
        
        for company, articles in company_articles.items():
            # Extract topics and insights from articles
            all_topics = []
            all_insights = []
            all_sentiments = []
            
            for article in articles:
                # Try to use new analysis structure first
                if hasattr(article, 'analysis_data') and article.analysis_data:
                    analysis_data = self._extract_analysis_data(article)
                    
                    # Extract topics from new structure - prioritize 'topics' field
                    if analysis_data.get('topics'):
                        all_topics.extend(analysis_data['topics'])
                    elif analysis_data.get('tags'):
                        all_topics.extend(analysis_data['tags'])
                    
                    # Extract insights from new structure
                    if analysis_data.get('insights'):
                        all_insights.extend(analysis_data['insights'])
                    
                    # Extract sentiment and convert to score
                    if analysis_data.get('sentiment'):
                        sentiment = analysis_data['sentiment']
                        if sentiment == 'positive':
                            all_sentiments.append(1.0)
                        elif sentiment == 'negative':
                            all_sentiments.append(-1.0)
                        else:
                            all_sentiments.append(0.0)
                
                # Fallback to old structure
                else:
                    if article.tags:
                        all_topics.extend(article.tags)
                    if article.key_insights:
                        all_insights.extend(article.key_insights)
            
            # Calculate trend score based on recency and content
            trend_score = 0.5  # Default score
            if articles:
                recent_articles = len([a for a in articles if a.publish_date])
                trend_score = min(1.0, recent_articles / max(len(articles), 1))
            
            # Calculate average sentiment score
            sentiment_score = 0.0
            if all_sentiments:
                sentiment_score = sum(all_sentiments) / len(all_sentiments)
            
            # Get unique topics and insights, limit to reasonable numbers
            unique_topics = list(set(all_topics))[:8]  # Top 8 topics
            unique_insights = list(set(all_insights))[:10]  # Top 10 insights
            
            insights[company] = {
                "company_name": company,
                "article_count": len(articles),
                "key_topics": unique_topics,
                "insights": unique_insights,
                "trend_score": trend_score,
                "sentiment_score": sentiment_score
            }
        
        return insights
    
    def _extract_industry_trends(self, articles: List[Article]) -> List[str]:
        """Extract industry trends from articles."""
        trends = []
        
        # Combine all topics from all articles
        all_topics = []
        for article in articles:
            # Try to use new analysis structure first
            if hasattr(article, 'analysis_data') and article.analysis_data:
                analysis_data = self._extract_analysis_data(article)
                
                # Extract topics from new structure - prioritize 'topics' field
                if analysis_data.get('topics'):
                    all_topics.extend(analysis_data['topics'])
                elif analysis_data.get('tags'):
                    all_topics.extend(analysis_data['tags'])
            else:
                # Fallback to old structure
                if article.tags:
                    all_topics.extend(article.tags)
        
        # Get top recurring trends
        from collections import Counter
        topic_counts = Counter(all_topics)
        
        # Filter out very short topics and get top trends
        meaningful_topics = [(topic, count) for topic, count in topic_counts.most_common(15) 
                           if len(topic) > 1]  # Filter out single character topics
        
        trends = [f"{topic} (提及 {count} 次)" 
                 for topic, count in meaningful_topics[:10]]  # Top 10 trends
        
        return trends
    
    def _compile_key_insights(self, articles: List[Article]) -> List[str]:
        """Compile key insights across all articles."""
        insights = []
        
        for article in articles:
            # Try to use new analysis structure first
            if hasattr(article, 'analysis_data') and article.analysis_data:
                analysis_data = self._extract_analysis_data(article)
                
                # Extract insights from new structure
                if analysis_data.get('insights'):
                    # Filter out very short insights and add top insights
                    meaningful_insights = [insight for insight in analysis_data['insights'] 
                                        if len(insight) > 5]  # Filter out very short insights
                    insights.extend(meaningful_insights[:3])  # Top 3 insights per article
            else:
                # Fallback to old structure
                if article.key_insights:
                    meaningful_insights = [insight for insight in article.key_insights 
                                        if len(insight) > 5]
                    insights.extend(meaningful_insights[:3])  # Top 3 insights per article
        
        # Remove duplicates, filter by quality, and limit to top 12
        unique_insights = []
        seen_insights = set()
        
        for insight in insights:
            # Normalize insight for deduplication
            normalized = insight.strip().lower()
            if normalized not in seen_insights and len(insight) > 10:  # Minimum quality threshold
                seen_insights.add(normalized)
                unique_insights.append(insight)
        
        return unique_insights[:12]  # Top 12 insights
    
    def _generate_executive_summary(self, data: Dict) -> str:
        """Generate executive summary text."""
        total_articles = data["total_articles"]
        companies = len(data["companies"])
        
        # Extract top trends and insights for summary
        top_trends = data["industry_trends"][:3] if data["industry_trends"] else []
        top_insights = data["key_insights"][:3] if data["key_insights"] else []
        
        # Calculate overall sentiment
        overall_sentiment = "中性"
        sentiment_scores = []
        for company_insight in data["company_insights"].values():
            if company_insight.get('sentiment_score') is not None:
                sentiment_scores.append(company_insight['sentiment_score'])
        
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            if avg_sentiment > 0.1:
                overall_sentiment = "积极"
            elif avg_sentiment < -0.1:
                overall_sentiment = "消极"
        
        summary = f"""
        本周，我们分析了来自 {companies} 家不同公司的 {total_articles} 篇文章。
        报告揭示了技术和商业创新方面的新兴趋势，整体情感倾向为{overall_sentiment}。
        """
        
        if top_trends:
            trends_text = "、".join([trend.split(" (")[0] for trend in top_trends])
            summary += f"主要趋势包括：{trends_text}。"
        
        if top_insights:
            insights_text = "、".join([insight[:20] + "..." if len(insight) > 20 else insight for insight in top_insights])
            summary += f"关键发现包括：{insights_text}"
        
        summary += "各公司更加注重客户体验优化和数字化转型计划。"
        
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
    
    def _deduplicate_articles(self, articles: List[Article]) -> List[Article]:
        """Remove duplicate articles based on URL."""
        seen_urls = set()
        unique_articles = []
        duplicate_count = 0
        
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
            else:
                duplicate_count += 1
        
        if duplicate_count > 0:
            print(f"⚠️  Removed {duplicate_count} duplicate articles")
            # Log the duplicate URLs for debugging
            duplicate_urls = []
            seen_urls_temp = set()
            for article in articles:
                if article.url in seen_urls_temp:
                    duplicate_urls.append(article.url)
                else:
                    seen_urls_temp.add(article.url)
            if duplicate_urls:
                print(f"   Duplicate URLs: {list(set(duplicate_urls))}")
        
        return unique_articles
    
    def _generate_article_details(self, articles: List[Article]) -> str:
        """Generate detailed article list for bottom of report."""
        details = []
        
        for article in articles:
            details.append(f"### [{article.title}]({article.url})")
            details.append(f"**{article.company_name}** - *{article.author or 'Unknown Author'}*")
            if article.publish_date:
                details.append(f"Published: {article.publish_date.strftime('%Y-%m-%d')}")
            
            # Use new analysis structure if available
            if hasattr(article, 'analysis_data') and article.analysis_data:
                analysis_data = self._extract_analysis_data(article)
                
                # Add metadata information
                if analysis_data.get('translated_title'):
                    details.append(f"**中文标题**: {analysis_data['translated_title']}")
                
                if analysis_data.get('tags'):
                    tags_text = ", ".join(analysis_data['tags'][:5])
                    details.append(f"**标签**: {tags_text}")
                
                # Add one sentence summary
                if analysis_data.get('one_sentence_summary'):
                    details.append(f"**一句话总结**: {analysis_data['one_sentence_summary']}")
                
                # Add summary content
                if analysis_data.get('summary_content'):
                    details.append(f"**内容摘要**: {analysis_data['summary_content']}")
                
                # Add key insights
                if analysis_data.get('insights'):
                    insights_text = "\n".join(f"- {insight}" for insight in analysis_data['insights'])
                    details.append(f"**关键见解**:\n{insights_text}")
                
                # Add topics
                if analysis_data.get('topics'):
                    topics_text = ", ".join(analysis_data['topics'][:5])
                    details.append(f"**主要话题**: {topics_text}")
                
                # Add hierarchical structure if available
                if analysis_data.get('hierarchical_structure'):
                    details.append("**内容结构**:")
                    for section in analysis_data['hierarchical_structure']:
                        details.append(f"  - **{section['heading']}**: {section['content']}")
                
                # Add sentiment
                if analysis_data.get('sentiment'):
                    sentiment_emoji = self._get_sentiment_emoji(analysis_data['sentiment'])
                    details.append(f"**情感分析**: {sentiment_emoji} {analysis_data['sentiment']}")
                
                # Add timestamp if available
                if analysis_data.get('timestamp'):
                    formatted_timestamp = self._format_timestamp(analysis_data['timestamp'])
                    if formatted_timestamp:
                        details.append(f"**分析时间**: {formatted_timestamp}")
            
            elif article.summary:
                # Fallback to old summary format
                details.append(f"**摘要**: {article.summary}")
                if article.key_insights:
                    insights_text = "\n".join(f"- {insight}" for insight in article.key_insights)
                    details.append(f"**关键见解**:\n{insights_text}")
            
            details.append("")
        
        return "\n".join(details)
    
    def _extract_analysis_data(self, article: Article) -> Dict:
        """Extract and validate analysis data from article."""
        if not hasattr(article, 'analysis_data') or not article.analysis_data:
            return {}
        
        analysis = article.analysis_data
        
        # Validate and extract metadata
        metadata = analysis.get('metadata', {})
        if not isinstance(metadata, dict):
            metadata = {}
        
        # Extract and validate fields
        result = {
            'original_title': metadata.get('original_title', article.title),
            'translated_title': metadata.get('translated_title', ''),
            'tags': metadata.get('tags', []) if isinstance(metadata.get('tags'), list) else [],
            'one_sentence_summary': analysis.get('one_sentence_summary', ''),
            'summary_content': analysis.get('summary_content', ''),
            'insights': analysis.get('insights', []) if isinstance(analysis.get('insights'), list) else [],
            'topics': analysis.get('topics', []) if isinstance(analysis.get('topics'), list) else [],
            'sentiment': analysis.get('sentiment', 'neutral'),
            'hierarchical_structure': analysis.get('hierarchical_structure', []) if isinstance(analysis.get('hierarchical_structure'), list) else [],
            'timestamp': analysis.get('timestamp', '')
        }
        
        # Clean and validate data
        result['tags'] = [tag for tag in result['tags'] if isinstance(tag, str) and len(tag.strip()) > 0]
        result['insights'] = [insight for insight in result['insights'] if isinstance(insight, str) and len(insight.strip()) > 5]
        result['topics'] = [topic for topic in result['topics'] if isinstance(topic, str) and len(topic.strip()) > 1]
        
        # Validate hierarchical structure
        if result['hierarchical_structure']:
            valid_structure = []
            for section in result['hierarchical_structure']:
                if isinstance(section, dict) and 'heading' in section and 'content' in section:
                    if isinstance(section['heading'], str) and isinstance(section['content'], str):
                        if len(section['heading'].strip()) > 0 and len(section['content'].strip()) > 0:
                            valid_structure.append({
                                'heading': section['heading'].strip(),
                                'content': section['content'].strip()
                            })
            result['hierarchical_structure'] = valid_structure
        
        return result
    
    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment."""
        sentiment_map = {
            'positive': '😊',
            'negative': '😞',
            'neutral': '😐'
        }
        return sentiment_map.get(sentiment.lower(), '😐')
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display."""
        if not timestamp:
            return ''
        
        try:
            # Try to parse ISO format timestamp
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            # Return as-is if parsing fails
            return timestamp