"""Email service for sending reports with SMTP integration."""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
from email.mime.application import MIMEApplication
import smtplib
import aiosmtplib
from datetime import datetime
from jinja2 import Environment, BaseLoader

from .settings import Settings


logger = logging.getLogger(__name__)


class EmailService:
    """Email service with SMTP integration and retry logic."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Setup email template renderer
        self.template_env = Environment(loader=BaseLoader())
        self.template_env.globals.update({
            'datetime': datetime,
            'len': len
        })
    
    async def send_report_email(
        self, 
        recipient_email: str, 
        report_paths: Dict[str, str], 
        report_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Send report via email with attachments.
        
        Args:
            recipient_email: Email address to send to
            report_paths: Dictionary with report file paths (markdown, pdf)
            report_metadata: Additional report information
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Prepare message
            message = await self._build_email_message(
                recipient_email, 
                report_paths, 
                report_metadata or {}
            )
            
            # Send email
            return await self._send_email(message, recipient_email)
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    async def send_bulk_reports(
        self, 
        recipients: List[str], 
        report_paths: Dict[str, str], 
        report_metadata: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """
        Send reports to multiple recipients.
        
        Args:
            recipients: List of email addresses
            report_paths: Report file paths
            report_metadata: Additional report info
            
        Returns:
            Dictionary mapping email to success status
        """
        results = {}
        
        # Send emails with some concurrency
        semaphore = asyncio.Semaphore(3)  # Limit concurrent connections
        
        async def send_single_email(recipient):
            async with semaphore:
                return await self.send_report_email(recipient, report_paths, report_metadata)
        
        # Gather all results
        tasks = [send_single_email(recipient) for recipient in recipients]
        email_results = await asyncio.gather(*tasks)
        
        for recipient, success in zip(recipients, email_results):
            results[recipient] = success
        
        return results
    
    async def _build_email_message(
        self, 
        recipient: str, 
        report_paths: Dict[str, str], 
        metadata: Dict
    ) -> MIMEMultipart:
        """Build the complete email message with attachments."""
        message = MIMEMultipart('related')
        
        # Email headers
        message['From'] = f"{self.settings.email_from_name} <{self.settings.email_username}>"
        message['To'] = recipient
        message['Subject'] = self._build_subject(metadata)
        message['Date'] = formatdate(localtime=True)
        
        # Email body
        body_text, body_html = self._build_email_body(metadata)
        
        # Add text part
        text_part = MIMEText(body_text, 'plain')
        message.attach(text_part)
        
        # Add HTML part
        html_part = MIMEText(body_html, 'html')
        message.attach(html_part)
        
        # Attach report files
        await self._attach_reports(message, report_paths)
        
        return message
    
    def _build_subject(self, metadata: Dict) -> str:
        """Build the email subject line."""
        date_str = datetime.now().strftime("%B %d, %Y")
        return f"Industry News Weekly Report - {date_str}"
    
    def _build_email_body(self, metadata: Dict) -> tuple:
        """Build both text and HTML email body."""
        companies = metadata.get('companies', [])
        total_articles = metadata.get('total_articles', 0)
        
        # Plain text version
        text_body = f"""
Weekly Industry News Report
Generated: {datetime.now().strftime('%B %d, %Y')}

SUMMARY: Analyzed {total_articles} articles from {len(companies)} companies

This week's report covers innovations and developments across the industry.

Attached files:
- PDF Report: Comprehensive formatted report
- Markdown Report: Raw data in markdown format

Report includes:
{chr(10).join([f"- {company}" for company in companies][:5])}
{idf len(companies) > 5 else f"...and {len(companies) - 5} more"}\n
Best regards,
Industry News Agent
"""
        
        # HTML version
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
            Weekly Industry News Report
        </h2>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #495057;">Report Summary</h3>
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            <p><strong>Total Articles Analyzed:</strong> {total_articles}</p>
            <p><strong>Companies Covered:</strong> {len(companies)}</p>
        </div>
        
        <h3>Companies Included:</h3>
        <ul>
            {''.join([f"<li>{company}</li>" for company in companies][:8])}
            {f'<li>...and {len(companies) - 8} more</li>' if len(companies) > 8 else ''}
        </ul>
        
        <div style="margin: 30px 0; padding: 20px; background-color: #e8f4f8; border-left: 4px solid #2c5aa0;">
            <p><strong>Report Features:</strong></p>
            <ul>
                <li>Executive summary of key findings</li>
                <li>Company-specific analysis and insights</li>
                <li>Industry trend identification</li>
                <li>Detailed article summaries</li>
            </ul>
        </div>
        
        <div style="margin-top: 30px;">
            <p><strong>Attached Files:</strong></p>
            <ul>
                <li><strong>PDF Report:</strong> Full PDF with professional formatting</li>
                <li><strong>Markdown Report:</strong> Raw content in markdown format</li>
            </ul>
        </div>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        
        <div style="font-size: 12px; color: #666;">
            <p>Best regards,</p>
            <p><strong>Industry News Agent</strong></p>
            <p><em>This report was automatically generated using our AI-powered analysis system.</em></p>
        </div>
    </div>
</body>
</html>
"""
        
        return text_body.strip(), html_body.strip()
    
    async def _attach_reports(self, message: MIMEMultipart, report_paths: Dict[str, str]) -> None:
        """Attach report files to the email."""
        for format_type, filepath in report_paths.items():
            if filepath and Path(filepath).exists():
                try:
                    await self._attach_file(message, filepath, format_type.upper())
                except Exception as e:
                    logger.warning(f"Failed to attach {format_type} report: {str(e)}")
    
    async def _attach_file(self, message: MIMEMultipart, filepath: str, description: str) -> None:
        """Attach a single file to the email."""
        file_path = Path(filepath)
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(file_data)
            encoders.encode_base64(attachment)
            
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{file_path.name}"'
            )
            attachment.add_header('Content-Description', description)
            
            message.attach(attachment)
            
            logger.info(f"Attached {file_path.name} to email")
            
        except Exception as e:
            logger.error(f"Error attaching file {filepath}: {str(e)}")
            raise
    
    async def _send_email(self, message: MIMEMultipart, recipient: str) -> bool:
        """Send the email using SMTP."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries + 1):
            try:
                # Connect and send
                await self._establish_connection_and_send(message, recipient)
                logger.info(f"Email sent successfully to {recipient}")
                return True
                
            except Exception as e:
                logger.warning(f"Email send attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"All email send attempts failed for {recipient}: {str(e)}")
                    return False
    
    async def _establish_connection_and_send(self, message: MIMEMultipart, recipient: str) -> None:
        """Establish SMTP connection and send message."""
        
        # Use aiohttp-friendly SMTP connector
        async with aiosmtplib.SMTP(
            hostname=self.settings.smtp_server,
            port=self.settings.smtp_port,
            use_tls=False,  # We'll handle TLS below
            timeout=30
        ) as smtp:
            
            # Start TLS if supported
            try:
                await smtp.starttls()
            except aiosmtplib.SMTPException:
                # TLS might not be supported or required
                pass
            
            # Authenticate
            await smtp.login(
                self.settings.email_username,
                self.settings.email_password
            )
            
            # Send message
            await smtp.send_message(message)
    
    def validate_email_settings(self) -> bool:
        """Validate email configuration."""
        required_fields = [
            'email_username',
            'email_password',
            'smtp_server',
            'smtp_port'
        ]
        
        for field in required_fields:
            if not getattr(self.settings, field):
                logger.error(f"Missing email configuration: {field}")
                return False
        
        try:
            # Quick test connection
            import smtplib
            with smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.settings.email_username, self.settings.email_password)
            return True
            
        except Exception as e:
            logger.error(f"Email settings validation failed: {str(e)}")
            return False