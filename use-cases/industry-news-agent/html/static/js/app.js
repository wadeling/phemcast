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
                        if (k === 'audio' && status.report_paths[k]) {
                            return `
                                <div style="margin: 10px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745;">
                                    <strong>🎧 Audio Report Available</strong><br>
                                    <small style="color: #666;">
                                        <a href="/download/${taskId}/audio" target="_blank" style="color: #007bff;">Direct Link</a>
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
            
            // 检查是否有音频文件，如果有则显示音频播放器并添加任务卡片
            console.log('Checking audio data:', status.report_paths);
            if (status.report_paths && status.report_paths.audio) {
                console.log('Audio data found:', status.report_paths.audio);
                // 调用全局函数显示音频播放器
                if (typeof showAudioPlayer === 'function') {
                    console.log('Calling showAudioPlayer function');
                    showAudioPlayer(`/download/${taskId}/audio`);
                } else {
                    console.error('showAudioPlayer function not found');
                }
                
                // Add podcast card for the completed summoning
                const taskData = {
                    task_id: taskId,
                    task_name: `Industry Intelligence ${taskId.substring(0, 8)}`,
                    description: `PHEMCAST summoned ${status.total_articles || 0} industry voices into compelling podcast narrative`,
                    audio_url: `/download/${taskId}/audio`,
                    created_at: new Date().toISOString(),
                    total_articles: status.total_articles || 0
                };
                
                if (typeof addTaskCard === 'function') {
                    addTaskCard(taskData);
                }
            } else {
                console.log('No audio data found or audio generation failed');
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
                    if (k === 'audio' && message.data.report_paths[k]) {
                        return `
                            <div style="margin: 10px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745;">
                                <strong>🎧 Audio Report Available</strong><br>
                                <small style="color: #666;">
                                    <a href="/download/${currentTaskId}/audio" target="_blank" style="color: #007bff;">Direct Link</a>
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
        
        // Add podcast card for the completed summoning (replaces old audio-container)
        console.log('WebSocket audio data:', message.data?.report_paths?.audio);
        if (message.data?.report_paths?.audio) {
            console.log('WebSocket: Audio data found, creating task card');
            
            // Add podcast card for the completed summoning
            const taskData = {
                task_id: currentTaskId,
                task_name: `Industry Intelligence ${currentTaskId.substring(0, 8)}`,
                description: `PHEMCAST summoned ${message.data?.total_articles || 0} industry voices into compelling podcast narrative`,
                audio_url: `/download/${currentTaskId}/audio`,
                created_at: new Date().toISOString(),
                total_articles: message.data?.total_articles || 0
            };
            
            if (typeof addTaskCard === 'function') {
                addTaskCard(taskData);
            }
        } else {
            console.log('WebSocket: No audio data or audio generation failed');
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

// 音频播放器相关函数已移除，现在使用task-card进行音频播放

// Task Cards Management
let taskCards = [];
let currentPlayingCard = null;

function createTaskCard(taskData) {
    const cardId = `task-card-${taskData.task_id}`;
    const card = document.createElement('div');
    card.className = 'task-card';
    card.id = cardId;
    card.dataset.taskId = taskData.task_id;
    
    const createdDate = new Date(taskData.created_at || Date.now());
    const formattedDate = createdDate.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
    });
    
    card.innerHTML = `
        <div class="task-card-header">
            <span class="task-card-tag">#Podcast</span>
            <span class="task-card-date">${formattedDate}</span>
        </div>
        <div class="task-card-title">${taskData.task_name || 'Industry Intelligence Podcast'}</div>
        <div class="task-card-description">${taskData.description || 'PHEMCAST summoned industry voices into compelling audio narrative'}</div>
        <div class="task-card-audio">
            <audio id="audio-${taskData.task_id}" preload="metadata">
                <source src="${taskData.audio_url || ''}" type="audio/mpeg">
            </audio>
        </div>
        <div class="task-card-controls">
            <div class="task-card-progress">
                <div class="task-card-progress-fill" id="progress-${taskData.task_id}"></div>
            </div>
        </div>
        <div class="task-card-time">
            <span id="current-time-${taskData.task_id}">0:00</span>
            <span id="duration-${taskData.task_id}">0:00</span>
        </div>
        <div class="task-card-buttons">
            <button class="task-card-btn secondary-btn" onclick="toggleShuffle('${taskData.task_id}')" title="Shuffle">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
                </svg>
            </button>
            <button class="task-card-btn secondary-btn" onclick="skipBackward('${taskData.task_id}')" title="Skip Backward">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/>
                </svg>
            </button>
            <button class="task-card-btn play-btn" onclick="togglePlay('${taskData.task_id}')" id="play-btn-${taskData.task_id}" title="Play">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7z"/>
                </svg>
            </button>
            <button class="task-card-btn secondary-btn" onclick="skipForward('${taskData.task_id}')" title="Skip Forward">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M13 6v12l8.5-6L13 6zM4 18l8.5-6L4 6v12z"/>
                </svg>
            </button>
            <button class="task-card-btn download-btn" onclick="downloadTaskAudio('${taskData.task_id}')" title="Download">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                </svg>
            </button>
        </div>
    `;
    
    // Setup audio event listeners
    const audio = card.querySelector('audio');
    if (audio) {
        audio.addEventListener('loadedmetadata', () => {
            updateDuration(taskData.task_id, audio.duration);
        });
        
        audio.addEventListener('timeupdate', () => {
            updateProgress(taskData.task_id, audio.currentTime, audio.duration);
        });
        
        audio.addEventListener('ended', () => {
            resetPlayButton(taskData.task_id);
        });
    }
    
    return card;
}

function addTaskCard(taskData) {
    const container = document.getElementById('taskCardsContainer');
    const noTasksMessage = document.getElementById('noTasksMessage');
    
    // Check if task card already exists
    const existingCard = document.getElementById(`task-card-${taskData.task_id}`);
    if (existingCard) {
        console.log(`Task card for ${taskData.task_id} already exists, skipping`);
        return;
    }
    
    if (noTasksMessage) {
        noTasksMessage.style.display = 'none';
    }
    
    const card = createTaskCard(taskData);
    container.appendChild(card);
    taskCards.push(taskData);
    
    // Scroll to the new card
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function togglePlay(taskId) {
    const audio = document.getElementById(`audio-${taskId}`);
    const playBtn = document.getElementById(`play-btn-${taskId}`);
    
    if (!audio) {
        console.log('Audio element not found for task:', taskId);
        return;
    }
    
    // Check if audio has a source (either src attribute or source element)
    const hasSource = audio.src || (audio.querySelector('source') && audio.querySelector('source').src);
    if (!hasSource) {
        console.log('No audio source available for task:', taskId);
        console.log('Audio element:', audio);
        console.log('Source element:', audio.querySelector('source'));
        return;
    }
    
    // Stop any currently playing audio
    if (currentPlayingCard && currentPlayingCard !== taskId) {
        const currentAudio = document.getElementById(`audio-${currentPlayingCard}`);
        const currentPlayBtn = document.getElementById(`play-btn-${currentPlayingCard}`);
        if (currentAudio) {
            currentAudio.pause();
            resetPlayButton(currentPlayingCard);
        }
    }
    
    if (audio.paused) {
        audio.play();
        playBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
            </svg>
        `;
        currentPlayingCard = taskId;
    } else {
        audio.pause();
        playBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
            </svg>
        `;
        currentPlayingCard = null;
    }
}

function resetPlayButton(taskId) {
    const playBtn = document.getElementById(`play-btn-${taskId}`);
    if (playBtn) {
        playBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
            </svg>
        `;
    }
    if (currentPlayingCard === taskId) {
        currentPlayingCard = null;
    }
}

function updateProgress(taskId, currentTime, duration) {
    const progressFill = document.getElementById(`progress-${taskId}`);
    const currentTimeEl = document.getElementById(`current-time-${taskId}`);
    
    if (progressFill && duration > 0) {
        const progress = (currentTime / duration) * 100;
        progressFill.style.width = `${progress}%`;
    }
    
    if (currentTimeEl) {
        currentTimeEl.textContent = formatTime(currentTime);
    }
}

function updateDuration(taskId, duration) {
    const durationEl = document.getElementById(`duration-${taskId}`);
    if (durationEl) {
        durationEl.textContent = formatTime(duration);
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function toggleShuffle(taskId) {
    // Placeholder for shuffle functionality
    console.log('Shuffle toggled for task:', taskId);
}

function skipBackward(taskId) {
    const audio = document.getElementById(`audio-${taskId}`);
    if (audio) {
        audio.currentTime = Math.max(0, audio.currentTime - 10);
    }
}

function skipForward(taskId) {
    const audio = document.getElementById(`audio-${taskId}`);
    if (audio) {
        audio.currentTime = Math.min(audio.duration, audio.currentTime + 10);
    }
}

function downloadTaskAudio(taskId) {
    const audio = document.getElementById(`audio-${taskId}`);
    if (audio && audio.src) {
        const link = document.createElement('a');
        link.href = audio.src;
        link.download = `phemcast_${taskId}.mp3`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
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
    
    // Load existing task cards (if any)
    loadExistingTaskCards();
});

async function loadExistingTaskCards() {
    console.log('Loading existing task cards...');
    
    try {
        const response = await fetch('/api/recent-tasks');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const tasks = data.tasks || [];
        
        console.log(`Loaded ${tasks.length} recent tasks from server`);
        
        if (tasks.length > 0) {
            // Clear the no-tasks message
            const noTasksMessage = document.getElementById('noTasksMessage');
            if (noTasksMessage) {
                noTasksMessage.style.display = 'none';
            }
            
            // Add each task as a card
            tasks.forEach(taskData => {
                console.log('Processing task data:', taskData);
                
                // Convert audio_url to download URL format if needed
                if (taskData.audio_url && !taskData.audio_url.startsWith('/download/')) {
                    taskData.audio_url = `/download/${taskData.task_id}/audio`;
                }
                
                console.log('Final audio_url:', taskData.audio_url);
                addTaskCard(taskData);
            });
            
            console.log(`Successfully loaded ${tasks.length} task cards`);
        } else {
            console.log('No recent tasks found, showing no-tasks message');
        }
        
    } catch (error) {
        console.error('Failed to load existing task cards:', error);
        // Don't show error to user, just log it and show no-tasks message
    }
}

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