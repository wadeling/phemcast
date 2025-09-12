// Internationalization (i18n) system for PHEMCAST
class I18n {
    constructor() {
        this.currentLanguage = localStorage.getItem('language') || 'en';
        this.translations = {
            en: {
                // Header
                'nav.features': 'Features',
                'nav.about': 'About',
                'nav.documentation': 'Documentation',
                'nav.support': 'Support',
                'header.welcome': 'Welcome,',
                'header.tasks': 'Tasks',
                'header.logout': 'Logout',
                'header.websocket.connecting': 'WebSocket: Connecting...',
                'header.websocket.connected': 'WebSocket: Connected',
                'header.websocket.disconnected': 'WebSocket: Disconnected',
                
                // Hero Section
                'hero.badge': 'AI-Powered Podcast Generator',
                'hero.title': 'Summon the voice of industry intelligence',
                'hero.subtitle': 'PHEMCAST transforms enterprise blogs into compelling podcasts. Our AI automatically gathers public voices, analyzes insights, and summons them into powerful audio narratives that command attention.',
                
                // Features
                'features.title': 'Powerful Features',
                'features.subtitle': 'Everything you need to create professional podcasts from industry content',
                'features.voice.title': 'Voice Cloning',
                'features.voice.desc': 'Create natural-sounding voice clones for authentic podcast narration',
                'features.podcast.title': 'Podcast Crafting',
                'features.podcast.desc': 'Transform industry insights into professional-grade podcasts with natural voice synthesis',
                'features.rapid.title': 'Rapid Summoning',
                'features.rapid.desc': 'Generate industry podcasts in minutes, not hours, with our optimized processing pipeline',
                'features.scheduling.title': 'Auto-Summon Scheduling',
                'features.scheduling.desc': 'Set up recurring podcast generation to stay ahead of industry trends automatically',
                'features.ethical.title': 'Respectful Harvesting',
                'features.ethical.desc': 'Ethical content gathering with built-in rate limiting and respectful data practices',
                
                // Form
                'form.title': 'Create Your Podcast',
                'form.subtitle': 'Enter company blog URLs to generate a professional podcast',
                'form.urls.label': 'Company Blog URLs',
                'form.urls.placeholder': 'Enter one URL per line...',
                'form.email.label': 'Email for Delivery (Optional)',
                'form.email.placeholder': 'your@email.com',
                'form.articles.label': 'Articles per Blog',
                'form.articles.placeholder': 'Select number of articles',
                'form.submit': 'Summon Voice',
                'form.submitting': 'Summoning...',
                'form.schedule': 'Schedule Recurring Summons',
                
                // Task Status
                'task.status.processing': 'Processing',
                'task.status.completed': 'Completed',
                'task.status.error': 'Error',
                'task.status.pending': 'Pending',
                'task.created': 'Task created',
                'task.started': 'Task started',
                'task.completed': 'Task completed',
                'task.failed': 'Task failed',
                'task.no_tasks': 'No recent tasks',
                'task.view_details': 'View Details',
                'task.download': 'Download',
                'task.section.title': 'Your Summoned Podcasts',
                'task.section.subtitle': 'Command your collection of industry intelligence podcasts',
                'task.no_podcasts.title': 'No podcasts summoned yet',
                'task.no_podcasts.desc': 'Summon your first industry podcast to see it appear here',
                
                // Messages
                'message.success': 'Success',
                'message.error': 'Error',
                'message.task_submitted': 'Task submitted successfully! You can check the task status by clicking the "Tasks" button.',
                'message.task_submission_failed': 'Task submission failed:',
                'message.no_task_id': 'No task ID returned',
                'message.websocket_connected': 'WebSocket connected',
                'message.websocket_disconnected': 'WebSocket disconnected',
                'message.websocket_error': 'WebSocket error',
                
                // Validation
                'validation.urls_required': 'Please enter at least one URL',
                'validation.invalid_url': 'Please enter a valid URL',
                'validation.email_required': 'Email is required',
                'validation.email_invalid': 'Please enter a valid email address',
                'validation.password_mismatch': 'Passwords do not match',
                'validation.username_required': 'Username is required',
                'validation.password_required': 'Password is required',
                
                // Login/Register
                'login.title': 'Login',
                'login.username': 'Username',
                'login.password': 'Password',
                'login.submit': 'Login',
                'login.register': 'Register',
                'login.forgot_password': 'Forgot Password?',
                'register.title': 'Create Account',
                'register.username': 'Username',
                'register.email': 'Email',
                'register.password': 'Password',
                'register.confirm_password': 'Confirm Password',
                'register.submit': 'Create Account',
                'register.invite_code': 'Invite Code',
                'register.verify_invite': 'Verify Invite Code',
                
                // Common
                'common.loading': 'Loading...',
                'common.error': 'Error',
                'common.success': 'Success',
                'common.cancel': 'Cancel',
                'common.close': 'Close',
                'common.save': 'Save',
                'common.delete': 'Delete',
                'common.edit': 'Edit',
                'common.back': 'Back',
                'common.next': 'Next',
                'common.previous': 'Previous',
                'common.yes': 'Yes',
                'common.no': 'No',
                'common.ok': 'OK',
                'common.cancel': 'Cancel',
                
                // Scheduled Tasks Modal
                'modal.title': 'Scheduled Task Management',
                'modal.create_task': 'Create New Scheduled Task',
                'modal.task_name': 'Task Name',
                'modal.task_name_placeholder': 'e.g., Weekly Industry Report',
                'modal.urls': 'URLs (one per line)',
                'modal.urls_placeholder': 'https://blog.openai.com\nhttps://blog.microsoft.com',
                'modal.email_recipients': 'Email Recipients',
                'modal.email_recipients_placeholder': 'Multiple emails separated by commas (optional)',
                'modal.schedule_frequency': 'Execution Frequency',
                'modal.schedule_daily': 'Daily',
                'modal.schedule_weekly': 'Weekly',
                'modal.schedule_monthly': 'Monthly',
                'modal.execution_time': 'Execution Time (UTC+8)',
                'modal.execution_date': 'Execution Date',
                'modal.create_button': 'Create Task',
                'modal.my_tasks': 'My Scheduled Tasks',
                'modal.loading': 'Loading...',
                'modal.close': 'Close',
                'modal.no_tasks': 'No scheduled tasks',
                'modal.please_login': 'Please login first',
                'modal.login_expired': 'Login expired, please login again',
                'modal.load_failed': 'Load failed',
                'modal.unknown_error': 'Unknown error',
                'modal.execution_plan': 'Execution Plan',
                'modal.status': 'Status',
                'modal.active': 'Active',
                'modal.paused': 'Paused',
                'modal.pause': 'Pause',
                'modal.start': 'Start',
                'modal.delete': 'Delete',
                'modal.daily': 'Daily',
                'modal.weekly': 'Weekly',
                'modal.monthly': 'Monthly',
                'modal.day': 'Day'
            },
            zh: {
                // Header
                'nav.features': '功能',
                'nav.about': '关于',
                'nav.documentation': '文档',
                'nav.support': '支持',
                'header.welcome': '欢迎，',
                'header.tasks': '任务',
                'header.logout': '退出',
                'header.websocket.connecting': 'WebSocket: 连接中...',
                'header.websocket.connected': 'WebSocket: 已连接',
                'header.websocket.disconnected': 'WebSocket: 已断开',
                
                // Hero Section
                'hero.badge': 'AI驱动的播客生成器',
                'hero.title': '召唤行业智能之声',
                'hero.subtitle': 'PHEMCAST将企业博客转化为引人入胜的播客。我们的AI自动收集公共声音，分析洞察，并将它们召唤成强大的音频叙事，吸引注意力。',
                
                // Features
                'features.title': '强大功能',
                'features.subtitle': '从行业内容创建专业播客所需的一切',
                'features.voice.title': '声音克隆',
                'features.voice.desc': '创建自然逼真的声音克隆，实现真实的播客叙述',
                'features.podcast.title': '播客制作',
                'features.podcast.desc': '将行业洞察转化为专业级播客，配备自然语音合成',
                'features.rapid.title': '快速召唤',
                'features.rapid.desc': '在几分钟内生成行业播客，而不是几小时，通过我们优化的处理管道',
                'features.scheduling.title': '自动召唤调度',
                'features.scheduling.desc': '设置定期播客生成，自动保持行业趋势领先',
                'features.ethical.title': '尊重式采集',
                'features.ethical.desc': '道德内容收集，内置速率限制和尊重数据实践',
                
                // Form
                'form.title': '创建您的播客',
                'form.subtitle': '输入公司博客URL以生成专业播客',
                'form.urls.label': '公司博客URL',
                'form.urls.placeholder': '每行输入一个URL...',
                'form.email.label': '投递邮箱（可选）',
                'form.email.placeholder': 'your@email.com',
                'form.articles.label': '每博客文章数',
                'form.articles.placeholder': '选择文章数量',
                'form.submit': '召唤声音',
                'form.submitting': '召唤中...',
                'form.schedule': '设置定期召唤',
                
                // Task Status
                'task.status.processing': '处理中',
                'task.status.completed': '已完成',
                'task.status.error': '错误',
                'task.status.pending': '等待中',
                'task.created': '任务已创建',
                'task.started': '任务已开始',
                'task.completed': '任务已完成',
                'task.failed': '任务失败',
                'task.no_tasks': '暂无最近任务',
                'task.view_details': '查看详情',
                'task.download': '下载',
                'task.section.title': '您召唤的播客',
                'task.section.subtitle': '掌控您的行业智能播客收藏',
                'task.no_podcasts.title': '尚未召唤任何播客',
                'task.no_podcasts.desc': '召唤您的第一个行业播客，它将出现在这里',
                
                // Messages
                'message.success': '成功',
                'message.error': '错误',
                'message.task_submitted': '任务提交成功！您可以点击"任务"按钮查看任务状态。',
                'message.task_submission_failed': '任务提交失败：',
                'message.no_task_id': '未返回任务ID',
                'message.websocket_connected': 'WebSocket已连接',
                'message.websocket_disconnected': 'WebSocket已断开',
                'message.websocket_error': 'WebSocket错误',
                
                // Validation
                'validation.urls_required': '请输入至少一个URL',
                'validation.invalid_url': '请输入有效的URL',
                'validation.email_required': '邮箱不能为空',
                'validation.email_invalid': '请输入有效的邮箱地址',
                'validation.password_mismatch': '两次输入的密码不一致',
                'validation.username_required': '用户名不能为空',
                'validation.password_required': '密码不能为空',
                
                // Login/Register
                'login.title': '登录',
                'login.username': '用户名',
                'login.password': '密码',
                'login.submit': '登录',
                'login.register': '注册',
                'login.forgot_password': '忘记密码？',
                'register.title': '创建账户',
                'register.username': '用户名',
                'register.email': '邮箱',
                'register.password': '密码',
                'register.confirm_password': '确认密码',
                'register.submit': '创建账户',
                'register.invite_code': '邀请码',
                'register.verify_invite': '验证邀请码',
                
                // Common
                'common.loading': '加载中...',
                'common.error': '错误',
                'common.success': '成功',
                'common.cancel': '取消',
                'common.close': '关闭',
                'common.save': '保存',
                'common.delete': '删除',
                'common.edit': '编辑',
                'common.back': '返回',
                'common.next': '下一步',
                'common.previous': '上一步',
                'common.yes': '是',
                'common.no': '否',
                'common.ok': '确定',
                'common.cancel': '取消',
                
                // Scheduled Tasks Modal
                'modal.title': '定时任务管理',
                'modal.create_task': '创建新定时任务',
                'modal.task_name': '任务名称',
                'modal.task_name_placeholder': '例如：每周行业报告',
                'modal.urls': 'URLs (每行一个)',
                'modal.urls_placeholder': 'https://blog.openai.com\nhttps://blog.microsoft.com',
                'modal.email_recipients': '邮件接收者',
                'modal.email_recipients_placeholder': '多个邮箱用逗号分隔（可选）',
                'modal.schedule_frequency': '执行频率',
                'modal.schedule_daily': '每天',
                'modal.schedule_weekly': '每周',
                'modal.schedule_monthly': '每月',
                'modal.execution_time': '执行时间 (东八区时间)',
                'modal.execution_date': '执行日期',
                'modal.create_button': '创建任务',
                'modal.my_tasks': '我的定时任务',
                'modal.loading': '加载中...',
                'modal.close': '关闭',
                'modal.no_tasks': '暂无定时任务',
                'modal.please_login': '请先登录',
                'modal.login_expired': '登录已过期，请重新登录',
                'modal.load_failed': '加载失败',
                'modal.unknown_error': '未知错误',
                'modal.execution_plan': '执行计划',
                'modal.status': '状态',
                'modal.active': '活跃',
                'modal.paused': '暂停',
                'modal.pause': '暂停',
                'modal.start': '启动',
                'modal.delete': '删除',
                'modal.daily': '每天',
                'modal.weekly': '每周',
                'modal.monthly': '每月',
                'modal.day': '号'
            }
        };
    }
    
    // Get translation for a key
    t(key, params = {}) {
        const translation = this.translations[this.currentLanguage][key] || key;
        return this.interpolate(translation, params);
    }
    
    // Interpolate parameters in translation
    interpolate(str, params) {
        return str.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return params[key] || match;
        });
    }
    
    // Set language
    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        this.updatePageLanguage();
        this.translatePage();
    }
    
    // Update HTML lang attribute
    updatePageLanguage() {
        document.documentElement.lang = this.currentLanguage;
    }
    
    // Translate all elements with data-i18n attribute
    translatePage() {
        const elements = document.querySelectorAll('[data-i18n]');
        console.log(`Found ${elements.length} elements to translate`);
        
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            // Debug: log if translation is missing
            if (translation === key) {
                console.warn(`Translation missing for key: ${key}`);
            }
            
            if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = translation;
            } else if (element.tagName === 'INPUT' && (element.type === 'text' || element.type === 'email' || element.type === 'password')) {
                element.placeholder = translation;
            } else if (element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else if (element.tagName === 'OPTION') {
                element.textContent = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // Update dynamic content in scheduled tasks modal
        if (typeof updateScheduleDay === 'function') {
            updateScheduleDay();
        }
    }
    
    // Get current language
    getCurrentLanguage() {
        return this.currentLanguage;
    }
    
    // Check if current language is Chinese
    isChinese() {
        return this.currentLanguage === 'zh';
    }
}

// Initialize global i18n instance
window.i18n = new I18n();

// Language switcher component
class LanguageSwitcher {
    constructor() {
        this.createSwitcher();
        this.bindEvents();
    }
    
    createSwitcher() {
        const switcher = document.createElement('div');
        switcher.className = 'language-switcher';
        switcher.innerHTML = `
            <button id="lang-en" class="lang-btn ${window.i18n.getCurrentLanguage() === 'en' ? 'active' : ''}">EN</button>
            <button id="lang-zh" class="lang-btn ${window.i18n.getCurrentLanguage() === 'zh' ? 'active' : ''}">中文</button>
        `;
        
        // Insert into header
        const headerActions = document.querySelector('.header-actions');
        if (headerActions) {
            headerActions.insertBefore(switcher, headerActions.firstChild);
        }
    }
    
    bindEvents() {
        document.getElementById('lang-en')?.addEventListener('click', () => {
            this.switchLanguage('en');
        });
        
        document.getElementById('lang-zh')?.addEventListener('click', () => {
            this.switchLanguage('zh');
        });
    }
    
    switchLanguage(lang) {
        window.i18n.setLanguage(lang);
        this.updateActiveButton(lang);
    }
    
    updateActiveButton(lang) {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`lang-${lang}`).classList.add('active');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize language switcher
    new LanguageSwitcher();
    
    // Translate page on load
    window.i18n.translatePage();
});
