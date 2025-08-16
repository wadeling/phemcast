"""Email service for sending reports with Tencent Cloud SES and SMTP integration."""
import asyncio
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
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
from .logging_config import get_logger


logger = get_logger(__name__)


class TencentCloudEmailService:
    """Tencent Cloud SES email service."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        self._initialized = False
        
    def _initialize_client(self):
        """Initialize Tencent Cloud SES client."""
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.ses.v20201002 import ses_client
            
            # Get credentials from settings
            secret_id = self.settings.tencent_cloud_secret_id
            secret_key = self.settings.tencent_cloud_secret_key
            
            if not secret_id or not secret_key:
                raise ValueError("Tencent Cloud API credentials not configured in settings")
            
            # Create credential object
            cred = credential.Credential(secret_id, secret_key)
            
            # Create HTTP profile
            http_profile = HttpProfile()
            http_profile.endpoint = "ses.tencentcloudapi.com"
            
            # Create client profile
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            
            # Create SES client
            region = self.settings.tencent_cloud_region
            self._client = ses_client.SesClient(cred, region, client_profile)
            self._initialized = True
            
            logger.info("Tencent Cloud SES client initialized successfully")
            
        except ImportError:
            logger.error("Tencent Cloud SDK not installed. Please install: pip install tencentcloud-sdk-python")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Tencent Cloud SES client: {str(e)}")
            raise
    
    async def send_report_email(
        self, 
        recipient_email: str, 
        report_paths: Dict[str, str], 
        report_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Send report via Tencent Cloud SES.
        
        Args:
            recipient_email: Email address to send to
            report_paths: Dictionary with report file paths (markdown, pdf)
            report_metadata: Additional report information
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self._initialized:
                self._initialize_client()
            
            # Build email content
            subject = self._build_subject(report_metadata or {})
            html_content = self._build_html_content(report_metadata or {})
            text_content = self._build_text_content(report_metadata or {})
            
            # Send email using Tencent Cloud SES
            return await self._send_tencent_email(
                recipient_email, subject, html_content, text_content, report_paths
            )
            
        except Exception as e:
            logger.error(f"Failed to send Tencent Cloud email to {recipient_email}: {str(e)}")
            return False
    
    async def _send_tencent_email(
        self, 
        recipient: str, 
        subject: str, 
        html_content: str, 
        text_content: str, 
        report_paths: Dict[str, str]
    ) -> bool:
        """Send email using Tencent Cloud SES."""
        try:
            from tencentcloud.ses.v20201002 import models
            
            # Create request object
            req = models.SendEmailRequest()
            
            # Prepare base parameters
            params = {
                "FromEmailAddress": self.settings.tencent_from_email,
                "Destination": [recipient],
                "Subject": subject
            }
            
            # Choose between template and direct content based on settings
            if self.settings.tencent_use_template and self.settings.tencent_template_id:
                # Use template mode
                params["Template"] = {
                    "TemplateID": self.settings.tencent_template_id,
                    "TemplateData": json.dumps({
                        "content": text_content,
                        "subject": subject,
                        "date": datetime.now().strftime("%B %d, %Y")
                    })
                }
                logger.debug(f"Using Tencent Cloud template: {self.settings.tencent_template_id}")
            else:
                # Use direct content mode
                params["Simple"] = {
                    "Html": html_content,
                    "Text": text_content
                }
                logger.debug("Using direct content mode (no template)")
            
            # Add attachments if any
            attachments = await self._prepare_attachments(report_paths)
            if attachments:
                params["Attachments"] = attachments
                logger.debug(f"Added {len(attachments)} attachments")
            
            req.from_json_string(json.dumps(params))
            
            # Send email
            resp = self._client.SendEmail(req)
            logger.info(f"Tencent Cloud email sent successfully to {recipient}: {resp.to_json_string()}")
            return True
            
        except Exception as e:
            logger.error(f"Tencent Cloud email send failed: {str(e)}")
            return False
    
    async def _prepare_attachments(self, report_paths: Dict[str, str]) -> List[Dict]:
        """Prepare attachments for Tencent Cloud SES."""
        import base64
        
        attachments = []
        
        for format_type, filepath in report_paths.items():
            if filepath and Path(filepath).exists():
                try:
                    with open(filepath, 'rb') as f:
                        file_data = f.read()
                    
                    # Check file size (should be under 4MB for Tencent Cloud SES)
                    file_size_mb = len(file_data) / (1024 * 1024)
                    if file_size_mb > 4:
                        logger.warning(f"Attachment {filepath} is too large ({file_size_mb:.2f}MB), skipping")
                        continue
                    
                    # Convert to Base64 as required by Tencent Cloud SES
                    content_base64 = base64.b64encode(file_data).decode('utf-8')
                    
                    attachment = {
                        "FileName": Path(filepath).name,
                        "Content": content_base64,  # Base64 encoded content
                        "ContentType": self._get_content_type(format_type)
                    }
                    attachments.append(attachment)
                    
                    logger.debug(f"Prepared attachment: {Path(filepath).name}, size: {file_size_mb:.2f}MB")
                    
                except Exception as e:
                    logger.warning(f"Failed to prepare attachment {format_type}: {str(e)}")
        
        return attachments
    
    def _get_content_type(self, format_type: str) -> str:
        """Get MIME content type for file format."""
        content_types = {
            'pdf': 'application/pdf',
            'markdown': 'text/markdown',
            'md': 'text/markdown'
        }
        return content_types.get(format_type.lower(), 'application/octet-stream')
    
    def _build_subject(self, metadata: Dict) -> str:
        """Build the email subject line."""
        date_str = datetime.now().strftime("%B %d, %Y")
        return f"Industry News Weekly Report - {date_str}"
    
    def _build_html_content(self, metadata: Dict) -> str:
        """Build HTML email content."""
        companies = metadata.get('companies', [])
        total_articles = metadata.get('total_articles', 0)
        
        return f"""
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
    
    def _build_text_content(self, metadata: Dict) -> str:
        """Build plain text email content."""
        companies = metadata.get('companies', [])
        total_articles = metadata.get('total_articles', 0)
        
        return f"""
Weekly Industry News Report
Generated: {datetime.now().strftime('%B %d, %Y')}

SUMMARY: Analyzed {total_articles} articles from {len(companies)} companies

This week's report covers innovations and developments across the industry.

Attached files:
- PDF Report: Comprehensive formatted report
- Markdown Report: Raw data in markdown format

Report includes:
{chr(10).join([f"- {company}" for company in companies][:5])}
{f"...and {len(companies) - 5} more" if len(companies) > 5 else ""}

Best regards,
Industry News Agent
""".strip()


class SMTPEmailService:
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
{f"...and {len(companies) - 5} more" if len(companies) > 5 else ""}\n
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


class EmailService:
    """Unified email service that can use either Tencent Cloud SES or SMTP."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.tencent_service = TencentCloudEmailService(settings)
        self.smtp_service = SMTPEmailService(settings)
        
        # Determine which service to use by default
        self.use_tencent = self._should_use_tencent()
    
    def _should_use_tencent(self) -> bool:
        """Determine if we should use Tencent Cloud SES."""
        # Check if Tencent Cloud credentials are available from settings
        tencent_available = all([
            getattr(self.settings, 'tencent_cloud_secret_id', None),
            getattr(self.settings, 'tencent_cloud_secret_key', None),
            getattr(self.settings, 'tencent_from_email', None)
        ])
        logger.debug(f"tencent_available: {tencent_available}, tencent_cloud_secret_id: {self.settings.tencent_cloud_secret_id}, tencent_cloud_secret_key: {self.settings.tencent_cloud_secret_key}, tencent_from_email: {self.settings.tencent_from_email}")
        # Check if SMTP settings are available
        smtp_available = all([
            getattr(self.settings, 'email_username', None),
            getattr(self.settings, 'email_password', None),
            getattr(self.settings, 'smtp_server', None),
            getattr(self.settings, 'smtp_port', None)
        ])
        
        # Prefer Tencent Cloud if available, fallback to SMTP
        if tencent_available:
            logger.info("Using Tencent Cloud SES as primary email service")
            return True
        elif smtp_available:
            logger.info("Using SMTP as primary email service")
            return False
        else:
            logger.warning("No email service configuration found")
            return False
    
    async def send_report_email(
        self, 
        recipient_email: str, 
        report_paths: Dict[str, str], 
        report_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Send report via email using the best available service.
        
        Args:
            recipient_email: Email address to send to
            report_paths: Dictionary with report file paths (markdown, pdf)
            report_metadata: Additional report information
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            logger.debug(f"Sending email to {recipient_email} using {self.use_tencent}")
            if self.use_tencent:
                return await self.tencent_service.send_report_email(
                    recipient_email, report_paths, report_metadata
                )
            else:
                return await self.smtp_service.send_report_email(
                    recipient_email, report_paths, report_metadata
                )
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
        if self.use_tencent:
            # Tencent Cloud SES doesn't have built-in bulk sending, so we'll send individually
            results = {}
            for recipient in recipients:
                success = await self.tencent_service.send_report_email(
                    recipient, report_paths, report_metadata
                )
                results[recipient] = success
            return results
        else:
            return await self.smtp_service.send_bulk_reports(
                recipients, report_paths, report_metadata
            )
    
    def validate_email_settings(self) -> bool:
        """Validate email configuration for the active service."""
        if self.use_tencent:
            try:
                self.tencent_service._initialize_client()
                return True
            except Exception as e:
                logger.error(f"Tencent Cloud SES validation failed: {str(e)}")
                return False
        else:
            return self.smtp_service.validate_email_settings()
    
    def switch_to_smtp(self):
        """Switch to SMTP service."""
        self.use_tencent = False
        logger.info("Switched to SMTP email service")
    
    def switch_to_tencent(self):
        """Switch to Tencent Cloud SES service."""
        self.use_tencent = True
        logger.info("Switched to Tencent Cloud SES email service")