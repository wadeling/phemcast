// Industry News Agent - Main JavaScript

let isSubmitting = false; // Flag to prevent duplicate submissions

// Initialize form with default values
function initializeForm() {
    const urlsTextarea = document.getElementById('urls');
    const maxArticlesSelect = document.getElementById('max_articles');
    
    // Set default URL if textarea is empty
    if (!urlsTextarea.value.trim()) {
        urlsTextarea.value = 'https://blog.openai.com';
    }
    
    // Set default max articles to 1
    maxArticlesSelect.value = '1';
    
    console.log('Form initialized with default values');
}

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
    updateProgress(10, 'Starting report generation...');
    
    try {
        const response = await fetch('/api/generate-report-form', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.task_id) {
            updateProgress(30, 'Task created successfully, monitoring progress...');
            loadingElement.style.display = 'none';
            resultElement.innerHTML = `
                <div class="result success">
                    <strong>✅ Report Generation Started</strong><br>
                    Task ID: ${result.task_id}<br>
                    <small>Processing ${document.getElementById('max_articles').value} article(s) from ${document.getElementById('urls').value.split('\n').filter(url => url.trim()).length} blog(s)</small><br><br>
                    <div id="status"></div>
                    <button onclick="checkStatus('${result.task_id}')" class="status-button">
                        Check Status
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
                <strong>❌ Error:</strong> ${error.message || 'Unknown error occurred'}
            </div>
        `;
    } finally {
        isSubmitting = false; // Reset flag regardless of success or error
    }
}

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

async function checkStatus(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}`);
        const status = await response.json();
        
        const statusDiv = document.getElementById('status');
        
        if (status.status === 'completed') {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <strong>✅ Completed!</strong><br>
                    Analyzed: ${status.total_articles || 0} articles<br>
                    ${status.report_paths ? Object.keys(status.report_paths).map(k => `
                        <a href="/api/download/${taskId}/${k}" 
                           target="_blank" class="download-link">Download ${k.toUpperCase()} Report</a><br>
                    `).join('') : ''}
                    ${status.email_sent ? '<br>📧 Sent to email' : ''}
                </div>
            `;
        } else if (status.status === 'error') {
            statusDiv.innerHTML = `
                <div class="status-item error-text">
                    <strong>Error:</strong> ${status.error || 'Processing failed'}
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <strong>⏳ Status: ${status.status}</strong><br>
                    <small>Please refresh in 30 seconds...</small>
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
                    Status check failed: ${error.message || 'Unknown error'}
                </div>
            `;
        }
    }
}

// Initialize form when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('reportForm');
    if (form) {
        form.addEventListener('submit', handleSubmit);
        initializeForm();
    }
});