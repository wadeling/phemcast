# Industry News Agent - Frontend Pages

This directory contains the frontend interface for the Industry News Agent system.

## 📁 Files

### Main Pages
- **`index.html`** - Main interface for comprehensive analysis
- **`quick-test.html`** - Optimized for quick testing with 1 article
- **`nav.html`** - Navigation page to choose testing mode

### JavaScript Files
- **`js/app.js`** - Main application logic
- **`js/quick-test.js`** - Quick test page logic

### Styles
- **`css/style.css`** - Main stylesheet

## 🚀 Quick Start

### 1. Quick Test (Recommended for First Use)
- **URL**: `/static/quick-test.html`
- **Default**: 1 article from OpenAI blog
- **Processing Time**: 2-5 minutes
- **Perfect for**: Testing the system, verifying configuration

### 2. Full Analysis
- **URL**: `/` (main page)
- **Default**: 1 article, customizable
- **Processing Time**: Depends on article count
- **Perfect for**: Production use, comprehensive analysis

### 3. Navigation
- **URL**: `/static/nav.html`
- **Purpose**: Choose between different testing modes

## 🎯 Features

### Quick Test Page
- ✅ Pre-filled with 1 article (OpenAI blog)
- ✅ Preset URL buttons for popular blogs
- ✅ Expected results display
- ✅ Progress tracking
- ✅ Quick status checking

### Main Page
- ✅ Customizable article count
- ✅ Multiple blog support
- ✅ Email delivery option
- ✅ Comprehensive configuration

### Common Features
- ✅ Real-time progress tracking
- ✅ Status monitoring
- ✅ Report download links
- ✅ Error handling
- ✅ Responsive design

## 🔧 Configuration

### Default Settings
- **Articles per blog**: 1 (Quick Test) / 5 (Main)
- **Default URL**: `https://blog.openai.com`
- **Processing**: Asynchronous with task monitoring

### Customization
- Change article count via dropdown
- Add multiple blog URLs
- Configure email for report delivery
- Monitor progress in real-time

## 📱 Usage

### For Testing
1. Use **Quick Test** page for first-time setup verification
2. Start with 1 article to ensure everything works
3. Check status and download reports
4. Verify email delivery (if configured)

### For Production
1. Use **Main** page for comprehensive analysis
2. Configure multiple blogs and articles
3. Set up email delivery
4. Monitor long-running tasks

## 🎨 Styling

### CSS Classes
- `.form-hint` - Form field hints
- `.quick-test` - Quick test section styling
- `.preset-urls` - URL preset buttons
- `.stats` - Statistics display
- `.nav-cards` - Navigation card layout

### Responsive Design
- Mobile-friendly layout
- Adaptive grid system
- Touch-friendly buttons
- Readable typography

## 🔍 Troubleshooting

### Common Issues
1. **Form not submitting**: Check browser console for errors
2. **Progress not updating**: Ensure JavaScript is enabled
3. **Status check failing**: Verify API endpoints are accessible

### Debug Mode
- Open browser developer tools
- Check console for JavaScript errors
- Monitor network requests
- Verify API responses

## 📚 API Integration

### Endpoints Used
- `POST /api/generate-report-form` - Submit form data
- `GET /api/task/{task_id}` - Check task status
- `GET /api/download/{task_id}/{format}` - Download reports

### Data Format
```javascript
{
    urls: "https://blog.openai.com",
    email: "user@example.com",
    max_articles: "1"
}
```

## 🚀 Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Advanced filtering options
- [ ] Report preview functionality
- [ ] Batch processing interface
- [ ] User authentication system
