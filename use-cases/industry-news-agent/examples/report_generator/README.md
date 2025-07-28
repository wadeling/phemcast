# Report Generator Example

This example demonstrates report generation in both Markdown and PDF formats.

## Features

- Markdown report generation with proper formatting
- PDF report generation using ReportLab
- Customizable report templates
- Table of contents generation
- Image and chart support

## Usage

```bash
# Generate Markdown report
python report_generator.py --format markdown --articles articles.json --output report.md

# Generate PDF report
python report_generator.py --format pdf --articles articles.json --output report.pdf
```

## Structure

- `report_generator.py` - Main report generation functionality
- `templates/` - Report templates (Markdown and HTML)
- `formatters.py` - Content formatting utilities
- `pdf_generator.py` - PDF generation with ReportLab
- `markdown_generator.py` - Markdown generation utilities

## Key Concepts

1. **Template System**: Jinja2 templates for consistent report formatting
2. **PDF Generation**: ReportLab for professional PDF output
3. **Content Organization**: Structured content with sections and subsections
4. **Metadata Handling**: Article metadata and summary information
5. **Customization**: Configurable report styles and layouts

## Report Structure

1. **Executive Summary**: High-level overview of key findings
2. **Company Analysis**: Per-company article summaries
3. **Trend Analysis**: Industry trends and patterns
4. **Key Insights**: Important takeaways and recommendations
5. **Appendix**: Detailed article information and sources 