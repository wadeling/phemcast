// Industry News Agent - Main JavaScript

let isSubmitting = false; // Flag to prevent duplicate submissions
let websocket = null; // WebSocket connection
let currentTaskId = null; // Current task ID being monitored

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
            currentTaskId = result.task_id; // Set current task ID for WebSocket monitoring
            updateProgress(30, 'Task created successfully, monitoring progress via WebSocket...');
            loadingElement.style.display = 'none';
            resultElement.innerHTML = `
                <div class="result success">
                    <strong>✅ Report Generation Started</strong><br>
                    Task ID: ${result.task_id}<br>
                    <small>Processing ${document.getElementById('max_articles').value} article(s) from ${document.getElementById('urls').value.split('\n').filter(url => url.trim()).length} blog(s)</small><br><br>
                    <div id="status">
                        <div class="status-item">
                            <strong>⏳ Status: Created</strong><br>
                            <small>Task created, waiting for processing to start...</small>
                        </div>
                    </div>
                    <button onclick="checkStatus('${result.task_id}')" class="status-button">
                        Manual Check Status
                    </button>
                    <small style="color: #666; display: block; margin-top: 10px;">
                        💡 Status updates automatically via WebSocket. Use manual check as backup.
                    </small>
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
                    ${status.report_paths ? Object.keys(status.report_paths).map(k => {
                        if (k === 'audio' && status.report_paths[k] && status.report_paths[k].success) {
                            return `
                                <div style="margin: 10px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745;">
                                    <strong>🎧 Audio Report Available</strong><br>
                                    <small style="color: #666;">
                                        ⏰ Valid for 24 hours • 
                                        <a href="/audio/${status.report_paths[k].access_token}" target="_blank" style="color: #007bff;">Direct Link</a>
                                    </small>
                                </div>
                            `;
                        } else if (k !== 'audio') {
                            return `
                                <a href="/download/${taskId}/${k}" 
                                   target="_blank" class="download-link">Download ${k.toUpperCase()} Report</a><br>
                            `;
                        }
                        return '';
                    }).join('') : ''}
                    ${status.email_sent ? '<br>📧 Sent to email' : ''}
                </div>
            `;
            
            // 检查是否有音频文件，如果有则显示音频播放器
            if (status.report_paths && status.report_paths.audio && status.report_paths.audio.success) {
                // 调用全局函数显示音频播放器
                if (typeof showAudioPlayer === 'function') {
                    showAudioPlayer(status.report_paths.audio);
                }
            } else {
                // 如果没有音频文件，隐藏音频播放器
                if (typeof hideAudioPlayer === 'function') {
                    hideAudioPlayer();
                }
            }
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

// WebSocket connection management
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // 根据当前页面地址确定 WebSocket 服务器地址
    let wsHost;
    
    // 检查是否在开发环境
    if (window.location.hostname === 'localhost') {
        if (window.location.port === '') {
            // 前端运行在 localhost:80 (nginx)，后端在 localhost:8000
            wsHost = 'localhost:8000';
        } else if (window.location.port === '8000') {
            // 直接访问后端
            wsHost = 'localhost:8000';
        } else {
            // 其他端口，尝试使用当前端口
            wsHost = window.location.host;
        }
    } else {
        // 生产环境，使用当前页面地址
        wsHost = window.location.host;
    }
    
    const wsUrl = `${protocol}//${wsHost}/ws`;
    
    console.log('Attempting to connect to WebSocket:', wsUrl);
    console.log('Current page location:', window.location.href);
    console.log('WebSocket host:', wsHost);
    
    try {
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function(event) {
            console.log('WebSocket connected successfully');
            // Update UI status
            if (typeof updateWebSocketStatus === 'function') {
                updateWebSocketStatus(true);
            }
            
            // Clear any existing ping interval
            if (window.pingInterval) {
                clearInterval(window.pingInterval);
            }
            
            // Send ping to keep connection alive
            window.pingInterval = setInterval(() => {
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                    try {
                        websocket.send(JSON.stringify({type: 'ping'}));
                        console.log('Ping sent to WebSocket');
                    } catch (e) {
                        console.error('Failed to send ping:', e);
                    }
                }
            }, 30000); // Ping every 30 seconds
        };
        
        websocket.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                console.log('WebSocket message received:', message);
                handleWebSocketMessage(message);
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        };
        
        websocket.onclose = function(event) {
            console.log('WebSocket disconnected:', event.code, event.reason);
            
            // Update UI status
            if (typeof updateWebSocketStatus === 'function') {
                updateWebSocketStatus(false);
            }
            
            // Clear ping interval
            if (window.pingInterval) {
                clearInterval(window.pingInterval);
                window.pingInterval = null;
            }
            
            // Handle different close codes
            if (event.code === 1006) {
                console.warn('WebSocket connection failed (1006). This usually means the server is not reachable.');
                console.log('Trying alternative connection methods...');
                
                // Try alternative WebSocket URLs
                tryAlternativeWebSocketUrls();
            } else {
                // Normal disconnect, try to reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            }
        };
        
        websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        // Try to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    }
}

function handleWebSocketMessage(message) {
    console.log('WebSocket message received:', message);
    
    if (message.type === 'task_update' && message.task_id === currentTaskId) {
        updateTaskStatusFromWebSocket(message);
    } else if (message.type === 'pong') {
        console.log('Pong received from server');
    } else {
        console.log('Unknown message type:', message.type);
    }
}

function updateTaskStatusFromWebSocket(message) {
    const statusDiv = document.getElementById('status');
    if (!statusDiv) return;
    
    if (message.status === 'completed') {
        statusDiv.innerHTML = `
            <div class="status-item">
                <strong>✅ Completed!</strong><br>
                Analyzed: ${message.data?.total_articles || 0} articles<br>
                ${message.data?.report_paths ? Object.keys(message.data.report_paths).map(k => {
                    if (k === 'audio' && message.data.report_paths[k] && message.data.report_paths[k].success) {
                        return `
                            <div style="margin: 10px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745;">
                                <strong>🎧 Audio Report Available</strong><br>
                                <small style="color: #666;">
                                    ⏰ Valid for 24 hours • 
                                    <a href="/audio/${message.data.report_paths[k].access_token}" target="_blank" style="color: #007bff;">Direct Link</a>
                                </small>
                            </div>
                        `;
                    } else if (k !== 'audio') {
                        return `
                            <a href="/download/${currentTaskId}/${k}" 
                               target="_blank" class="download-link">Download ${k.toUpperCase()} Report</a><br>
                        `;
                    }
                    return '';
                }).join('') : ''}
                ${message.data?.email_sent ? '<br>📧 Sent to email' : ''}
            </div>
        `;
        
        // Show audio player if available
        if (message.data?.report_paths?.audio?.success) {
            if (typeof showAudioPlayer === 'function') {
                showAudioPlayer(message.data.report_paths.audio);
            }
        }
        
        // Hide loading indicator
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
    } else if (message.status === 'error') {
        statusDiv.innerHTML = `
            <div class="status-item error-text">
                <strong>Error:</strong> ${message.error || 'Processing failed'}
            </div>
        `;
        
        // Hide loading indicator
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
    } else if (message.status === 'processing') {
        statusDiv.innerHTML = `
            <div class="status-item">
                <strong>⏳ Status: Processing</strong><br>
                <small>Task is currently being processed...</small>
            </div>
        `;
    }
}

// Initialize form when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('reportForm');
    if (form) {
        form.addEventListener('submit', handleSubmit);
        initializeForm();
    }
    
    // Connect to WebSocket
    connectWebSocket();
});

// Try alternative WebSocket URLs when primary connection fails
function tryAlternativeWebSocketUrls() {
    const alternatives = [
        'ws://localhost:8000/ws',
        'ws://127.0.0.1:8000/ws',
        'ws://localhost/ws'
    ];
    
    console.log('Trying alternative WebSocket URLs:', alternatives);
    
    for (let i = 0; i < alternatives.length; i++) {
        setTimeout(() => {
            tryAlternativeConnection(alternatives[i]);
        }, i * 2000); // Try each alternative with 2 second delay
    }
}

function tryAlternativeConnection(wsUrl) {
    console.log('Trying alternative connection:', wsUrl);
    
    try {
        const altWebSocket = new WebSocket(wsUrl);
        
        altWebSocket.onopen = function(event) {
            console.log('Alternative WebSocket connected:', wsUrl);
            // Replace the main websocket
            if (websocket) {
                websocket.close();
            }
            websocket = altWebSocket;
            
            // Update UI status
            if (typeof updateWebSocketStatus === 'function') {
                updateWebSocketStatus(true);
            }
            
            // Setup ping interval
            if (window.pingInterval) {
                clearInterval(window.pingInterval);
            }
            window.pingInterval = setInterval(() => {
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                    try {
                        websocket.send(JSON.stringify({type: 'ping'}));
                        console.log('Ping sent to alternative WebSocket');
                    } catch (e) {
                        console.error('Failed to send ping to alternative WebSocket:', e);
                    }
                }
            }, 30000);
            
            // Setup other event handlers
            altWebSocket.onmessage = websocket.onmessage;
            altWebSocket.onclose = websocket.onclose;
            altWebSocket.onerror = websocket.onerror;
        };
        
        altWebSocket.onclose = function(event) {
            console.log('Alternative WebSocket failed:', wsUrl, event.code);
        };
        
        altWebSocket.onerror = function(error) {
            console.log('Alternative WebSocket error:', wsUrl, error);
        };
        
    } catch (error) {
        console.error('Failed to create alternative WebSocket:', wsUrl, error);
    }
}