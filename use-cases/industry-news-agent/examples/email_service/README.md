# Email Service Example

This example demonstrates email functionality for sending generated reports.

## Features

- SMTP email sending with authentication
- HTML and plain text email support
- File attachment handling (PDF and Markdown)
- Email templates with Jinja2
- Error handling and retry logic

## Usage

```bash
# Test email sending
python email_service.py --to user@example.com --report-path reports/weekly_report.pdf
```

## Configuration

Set up your email credentials in `.env`:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

## Structure

- `email_service.py` - Main email sending functionality
- `templates/` - Email HTML templates
- `attachments.py` - File attachment handling
- `validators.py` - Email validation

## Key Concepts

1. **SMTP Configuration**: Secure SMTP connection with authentication
2. **Template Rendering**: Jinja2 templates for email content
3. **File Attachments**: Handling PDF and Markdown file attachments
4. **Error Handling**: Retry logic for failed email sends
5. **Email Validation**: Proper email address validation 