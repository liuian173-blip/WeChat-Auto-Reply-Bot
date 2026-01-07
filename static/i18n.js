// 多语言配置
const i18n = {
    zh: {
        // 页面标题
        pageTitle: '微信AI助手 - 控制台',
        dashboardTitle: '性能监控仪表板',
        
        // 头部
        headerTitle: '🤖 微信AI助手控制台',
        statusRunning: '✓ 服务运行中',
        backToHome: '← 返回首页',
        
        // 系统状态卡片
        systemStatus: '系统状态',
        apiKey: 'API Key',
        startTime: '启动时间',
        runningPort: '运行端口',
        uptime: '运行时长',
        loading: '加载中...',
        minutes: '分钟',
        
        // 性能监控卡片
        performanceMonitor: '性能监控',
        avgResponseTime: '平均响应时间',
        totalRequests: '总请求数',
        cacheHitRate: '缓存命中率',
        slowRequests: '慢请求',
        timeoutRequests: '超时请求',
        
        // 缓存状态卡片
        cacheStatus: '缓存状态',
        memoryCache: '内存缓存',
        dbCache: '数据库缓存',
        cacheExpiry: '缓存过期',
        maxCapacity: '最大容量',
        items: '条',
        
        // 自动清理卡片
        autoCleanup: '自动清理',
        runningStatus: '运行状态',
        elapsed: '已运行',
        remaining: '剩余时间',
        cleanupCount: '清理次数',
        cleanedItems: '已清理数据',
        times: '次',
        
        // 快速操作
        quickActions: '快速操作',
        perfDashboard: '📊 性能仪表板',
        runCleanupNow: '🧹 立即清理',
        cacheDetails: '💾 缓存详情',
        cleanupDetails: '📈 清理详情',
        healthCheck: '❤️ 健康检查',
        stopService: '⏻ 停止服务',
        
        // 微信配置
        wechatConfig: '微信公众号配置',
        serverUrl: '服务器URL',
        token: 'Token',
        encryption: '消息加解密',
        plaintextMode: '明文模式',
        
        // 页脚
        footerText: '智谱AI微信助手 v3.5',
        lastUpdate: '最后更新',
        
        // 仪表板
        requestTypeStats: '请求类型统计',
        typeColumn: '类型',
        requestCount: '请求数',
        avgDuration: '平均耗时',
        maxDuration: '最大耗时',
        
        bottleneckAnalysis: '性能瓶颈分析',
        component: '组件',
        operation: '操作',
        callCount: '调用次数',
        
        slowestRequests: '最慢的请求',
        user: '用户',
        duration: '耗时',
        status: '状态',
        time: '时间',
        noData: '暂无数据',
        
        dataUpdateTime: '数据更新时间',
        apiInterface: 'API接口',
        
        // 对话框
        confirmCleanup: '确定要立即执行清理吗？',
        cleanupComplete: '清理完成！',
        cleanupFailed: '清理失败',
        requestFailed: '请求失败',
        
        cacheStatsTitle: '缓存统计信息：',
        
        cleanupStatusTitle: '清理状态：',
        
        healthCheckTitle: '健康检查：',
        service: '服务',
        featuresStatus: '功能状态',
        performance: '性能',
        
        confirmShutdown: '确定要关闭服务器吗？\n关闭后需要手动重启！',
        shuttingDown: '服务正在关闭...',
        shutdownFailed: '关闭失败',
        
        // 状态
        running: '运行中',
        stopped: '已停止',
        success: '成功',
        failed: '失败',
    },
    
    en: {
        // Page titles
        pageTitle: 'WeChat AI Assistant - Console',
        dashboardTitle: 'Performance Monitor Dashboard',
        
        // Header
        headerTitle: '🤖 WeChat AI Assistant Console',
        statusRunning: '✓ Service Running',
        backToHome: '← Back to Home',
        
        // System status card
        systemStatus: 'System Status',
        apiKey: 'API Key',
        startTime: 'Start Time',
        runningPort: 'Port',
        uptime: 'Uptime',
        loading: 'Loading...',
        minutes: 'min',
        
        // Performance monitor card
        performanceMonitor: 'Performance Monitor',
        avgResponseTime: 'Avg Response Time',
        totalRequests: 'Total Requests',
        cacheHitRate: 'Cache Hit Rate',
        slowRequests: 'Slow Requests',
        timeoutRequests: 'Timeout Requests',
        
        // Cache status card
        cacheStatus: 'Cache Status',
        memoryCache: 'Memory Cache',
        dbCache: 'Database Cache',
        cacheExpiry: 'Cache TTL',
        maxCapacity: 'Max Capacity',
        items: 'items',
        
        // Auto cleanup card
        autoCleanup: 'Auto Cleanup',
        runningStatus: 'Status',
        elapsed: 'Elapsed',
        remaining: 'Remaining',
        cleanupCount: 'Cleanup Count',
        cleanedItems: 'Items Cleaned',
        times: 'times',
        
        // Quick actions
        quickActions: 'Quick Actions',
        perfDashboard: '📊 Performance Dashboard',
        runCleanupNow: '🧹 Run Cleanup',
        cacheDetails: '💾 Cache Details',
        cleanupDetails: '📈 Cleanup Details',
        healthCheck: '❤️ Health Check',
        stopService: '⏻ Stop Service',
        
        // WeChat config
        wechatConfig: 'WeChat Official Account Config',
        serverUrl: 'Server URL',
        token: 'Token',
        encryption: 'Message Encryption',
        plaintextMode: 'Plaintext Mode',
        
        // Footer
        footerText: 'Zhipu AI WeChat Assistant v3.5',
        lastUpdate: 'Last Update',
        
        // Dashboard
        requestTypeStats: 'Request Type Statistics',
        typeColumn: 'Type',
        requestCount: 'Count',
        avgDuration: 'Avg Duration',
        maxDuration: 'Max Duration',
        
        bottleneckAnalysis: 'Bottleneck Analysis',
        component: 'Component',
        operation: 'Operation',
        callCount: 'Call Count',
        
        slowestRequests: 'Slowest Requests',
        user: 'User',
        duration: 'Duration',
        status: 'Status',
        time: 'Time',
        noData: 'No data available',
        
        dataUpdateTime: 'Data Update Time',
        apiInterface: 'API Interface',
        
        // Dialogs
        confirmCleanup: 'Are you sure you want to run cleanup now?',
        cleanupComplete: 'Cleanup completed!',
        cleanupFailed: 'Cleanup failed',
        requestFailed: 'Request failed',
        
        cacheStatsTitle: 'Cache Statistics:',
        
        cleanupStatusTitle: 'Cleanup Status:',
        
        healthCheckTitle: 'Health Check:',
        service: 'Service',
        featuresStatus: 'Features Status',
        performance: 'Performance',
        
        confirmShutdown: 'Are you sure you want to shutdown the server?\nYou need to restart it manually!',
        shuttingDown: 'Server is shutting down...',
        shutdownFailed: 'Shutdown failed',
        
        // Status
        running: 'Running',
        stopped: 'Stopped',
        success: 'Success',
        failed: 'Failed',
    }
};

// 当前语言
let currentLang = localStorage.getItem('language') || 'zh';

// 获取翻译文本
function t(key) {
    return i18n[currentLang][key] || key;
}

// 切换语言
function switchLanguage(lang) {
    if (!lang || !i18n[lang]) {
        console.error('Invalid language:', lang);
        return;
    }
    
    currentLang = lang;
    localStorage.setItem('language', lang);
    
    console.log('Switching to language:', lang);
    
    // 立即更新页面语言
    updatePageLanguage();
    
    // 延迟一点再刷新数据，确保DOM已更新
    setTimeout(() => {
        // 如果页面有 loadStatus 函数，重新加载数据（首页）
        if (typeof loadStatus === 'function') {
            console.log('Reloading status...');
            loadStatus();
        }
        
        // 如果页面有 loadDashboard 函数，重新加载数据（仪表板）
        if (typeof loadDashboard === 'function') {
            console.log('Reloading dashboard...');
            loadDashboard();
        }
    }, 100);
}

// 更新页面语言
function updatePageLanguage() {
    console.log('Updating page language to:', currentLang);
    
    // 更新所有带有 data-i18n 属性的元素
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = t(key);
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            element.placeholder = translation;
        } else {
            // 保留元素的子元素（如图标）
            const children = Array.from(element.children);
            element.textContent = translation;
            // 重新添加子元素
            children.forEach(child => element.appendChild(child));
        }
    });
    
    // 更新页面标题
    if (window.location.pathname === '/dashboard') {
        document.title = t('dashboardTitle');
    } else {
        document.title = t('pageTitle');
    }
    
    // 更新语言按钮状态
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        const btnLang = btn.getAttribute('data-lang');
        if (btnLang === currentLang) {
            btn.classList.add('active');
        }
    });
    
    console.log('Page language updated');
}

// 页面加载时初始化语言
document.addEventListener('DOMContentLoaded', function() {
    console.log('i18n.js loaded, current language:', currentLang);
    updatePageLanguage();
});