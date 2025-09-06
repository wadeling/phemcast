// Quick Test Page - Industry News Agent

let isSubmitting = false; // Flag to prevent duplicate submissions

// Initialize form with default values
function initializeForm() {
    const urlsTextarea = document.getElementById('urls');
    const maxArticlesSelect = document.getElementById('max_articles');
    
    // Set default URL if textarea is empty
    if (!urlsTextarea.value.trim()) {
        urlsTextarea.value = 'https://wiz.io/blog';
    }
    
    // Set default max articles to 1
    maxArticlesSelect.value = '1';
    
    // Update article count display
    updateArticleCount();
    
    console.log('Quick test form initialized with default values');
}

// Update article count display
function updateArticleCount() {
    const maxArticles = document.getElementById('max_articles').value;
    const articleCount = document.getElementById('article-count');
    if (articleCount) {
        articleCount.textContent = maxArticles;
    }
}

// Set URL from preset buttons
function setUrl(url) {
    document.getElementById('urls').value = url;
    console.log(`URL set to: ${url}`);
}

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();
    
    // Prevent duplicate submissions
    if (isSubmitting) {
        console.log('Form submission already in progress, ignoring duplicate click');
        return;
    }
    
    isSubmitting = true;
    
    const formData = new FormData();
    formData.append('urls', document.getElementById('urls').value);
    const email = document.getElementById('email').value;
    if (email) formData.append('email', email);
    formData.append('max_articles', document.getElementById('max_articles').value);
    
    const loadingElement = document.getElementById('loading');
    const resultElement = document.getElementById('result');
    
    loadingElement.style.display = 'block';
    resultElement.innerHTML = '';
    
    // Show initial progress
    updateProgress(10, 'Starting quick test...');
    
    try {
        const response = await fetch('/api/generate-report-form', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.task_id) {
            updateProgress(30, 'Task created successfully, monitoring progress...');
            loadingElement.style.display = 'none';
            
            const urlCount = document.getElementById('urls').value.split('\n').filter(url => url.trim()).length;
            const articleCount = document.getElementById('max_articles').value;
            
            resultElement.innerHTML = `
                <div class="result success">
                    <strong>✅ Quick Test Started!</strong><br>
                    Task ID: ${result.task_id}<br>
                    <small>Processing ${articleCount} article(s) from ${urlCount} blog(s)</small><br>
                    <small>Expected completion: 2-5 minutes</small><br><br>
                    <div id="status"></div>
                    <button onclick="checkStatus('${result.task_id}')" class="status-button">
                        🔍 Check Status
                    </button>
                    <button onclick="location.reload()" class="status-button" style="background: #6c757d; margin-left: 10px;">
                        🆕 New Test
                    </button>
                </div>
            `;
        } else {
            throw new Error('No task ID returned');
        }
    } catch (error) {
        updateProgress(0, 'Error occurred');
        loadingElement.style.display = 'none';
        resultElement.innerHTML = `
            <div class="result error">
                <strong>❌ Error:</strong> ${error.message || 'Unknown error occurred'}<br>
                <small>Please check your configuration and try again</small>
            </div>
        `;
    } finally {
        isSubmitting = false; // Reset flag regardless of success or error
    }
}

// Update progress bar and status message
function updateProgress(percentage, message) {
    const progressFill = document.getElementById('progress-fill');
    const currentStep = document.getElementById('current-step');
    
    if (progressFill) {
        progressFill.style.width = percentage + '%';
    }
    
    if (currentStep) {
        currentStep.textContent = message;
    }
}

// Check task status
async function checkStatus(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}`);
        const status = await response.json();
        
        const statusDiv = document.getElementById('status');
        
        if (status.status === 'completed') {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <strong>🎉 Quick Test Completed!</strong><br>
                    Analyzed: ${status.total_articles || 0} articles<br>
                    Processing Time: ~${status.processing_time || 'Unknown'}<br><br>
                    <strong>📄 Download Reports:</strong><br>
                    ${status.report_paths ? Object.keys(status.report_paths).map(k => `
                        <a href="/download/${taskId}/${k}" 
                           target="_blank" class="download-link">📥 Download ${k.toUpperCase()} Report</a><br>
                    `).join('') : ''}
                    ${status.email_sent ? '<br>📧 Report sent to email' : ''}
                    <br><br>
                    <small>💡 Tip: Try increasing the article count or adding more blogs for a comprehensive analysis</small>
                </div>
            `;
        } else if (status.status === 'error') {
            statusDiv.innerHTML = `
                <div class="status-item error-text">
                    <strong>❌ Error:</strong> ${status.error || 'Processing failed'}<br>
                    <small>Please check the logs or try with a different URL</small>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <strong>⏳ Status: ${status.status}</strong><br>
                    <small>Please wait, this should complete in 2-5 minutes...</small>
                </div>
            `;
            
            if (status.status === 'processing') {
                setTimeout(() => checkStatus(taskId), 10000); // Check every 10 seconds
            }
        }
    } catch (error) {
        const statusDiv = document.getElementById('status');
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="status-item error-text">
                    Status check failed: ${error.message || 'Unknown error'}<br>
                    <small>Please try again or refresh the page</small>
                </div>
            `;
        }
    }
}

// Initialize form when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('reportForm');
    const maxArticlesSelect = document.getElementById('max_articles');
    
    if (form) {
        form.addEventListener('submit', handleSubmit);
        initializeForm();
    }
    
    if (maxArticlesSelect) {
        maxArticlesSelect.addEventListener('change', updateArticleCount);
    }
});
