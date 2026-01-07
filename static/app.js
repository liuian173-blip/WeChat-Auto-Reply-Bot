// 全局变量
let autoRefreshInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadStatus();
    startAutoRefresh();
});

// 加载系统状态
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const result = await response.json();
        
        if (result.success) {
            updateUI(result.data);
            updateTimestamp(result.timestamp);
        } else {
            console.error('加载状态失败:', result);
        }
    } catch (error) {
        console.error('请求失败:', error);
    }
}

// 更新UI
function updateUI(data) {
    // 系统状态
    if (data.system) {
        document.getElementById('api-key').textContent = data.system.api_key;
        document.getElementById('start-time').textContent = data.system.start_time;
        document.getElementById('port').textContent = data.system.port;
        document.getElementById('uptime').textContent = data.system.uptime_minutes + ' ' + t('minutes');
    }
    
    // 性能监控
    if (data.performance) {
        const perfCard = document.getElementById('performance-card');
        const avgResponse = data.performance.avg_response_time_ms || 0;
        const avgResponseEl = document.getElementById('avg-response');
        
        // 更新响应时间
        avgResponseEl.innerHTML = avgResponse + '<span style="font-size: 24px;">ms</span>';
        
        // 设置颜色
        avgResponseEl.className = 'value';
        if (avgResponse < 3000) {
            avgResponseEl.classList.add('success');
        } else if (avgResponse < 4500) {
            avgResponseEl.classList.add('warning');
        } else {
            avgResponseEl.classList.add('error');
        }
        
        document.getElementById('total-requests').textContent = data.performance.total_requests || 0;
        document.getElementById('cache-hit-rate').textContent = (data.performance.cache_hit_rate || 0) + '%';
        
        const slowRequests = data.performance.slow_requests || 0;
        const slowEl = document.getElementById('slow-requests');
        slowEl.textContent = slowRequests;
        slowEl.className = 'stat-value ' + (slowRequests > 0 ? 'warning' : 'success');
        
        const timeoutRequests = data.performance.timeout_requests || 0;
        const timeoutEl = document.getElementById('timeout-requests');
        timeoutEl.textContent = timeoutRequests;
        timeoutEl.className = 'stat-value ' + (timeoutRequests > 0 ? 'error' : 'success');
        
        perfCard.style.opacity = '1';
    } else {
        document.getElementById('performance-card').style.opacity = '0.6';
        document.getElementById('avg-response').innerHTML = '0<span style="font-size: 24px;">ms</span>';
    }
    
    // 缓存状态
    if (data.cache) {
        document.getElementById('memory-cache').innerHTML = data.cache.memory_size + ' <span data-i18n="items">' + t('items') + '</span>';
        document.getElementById('db-cache').innerHTML = (data.cache.db_size || 0) + ' <span data-i18n="items">' + t('items') + '</span>';
        document.getElementById('cache-ttl').innerHTML = data.cache.ttl_minutes + ' <span data-i18n="minutes">' + t('minutes') + '</span>';
        document.getElementById('cache-max').innerHTML = data.cache.max_size + ' <span data-i18n="items">' + t('items') + '</span>';
    }
    
    // 清理状态
    if (data.cleanup) {
        const running = data.cleanup.running;
        const statusEl = document.getElementById('cleanup-status');
        statusEl.textContent = running ? t('running') : t('stopped');
        statusEl.className = 'stat-value ' + (running ? 'success' : 'error');
        
        document.getElementById('cleanup-elapsed').innerHTML = data.cleanup.elapsed_minutes + ' <span data-i18n="minutes">' + t('minutes') + '</span>';
        document.getElementById('cleanup-remaining').innerHTML = data.cleanup.remaining_minutes + ' <span data-i18n="minutes">' + t('minutes') + '</span>';
        document.getElementById('cleanup-count').innerHTML = data.cleanup.session_cleanups + ' <span data-i18n="times">' + t('times') + '</span>';
        document.getElementById('cleanup-items').innerHTML = data.cleanup.total_items_cleaned + ' <span data-i18n="items">' + t('items') + '</span>';
        
        // 更新进度条
        const total = data.cleanup.elapsed_minutes + data.cleanup.remaining_minutes;
        const progress = total > 0 ? (data.cleanup.elapsed_minutes / total * 100) : 0;
        document.getElementById('cleanup-progress').style.width = progress + '%';
        
        document.getElementById('cleanup-card').style.display = 'block';
    } else {
        document.getElementById('cleanup-card').style.display = 'none';
    }
}

// 更新时间戳
function updateTimestamp(timestamp) {
    document.getElementById('last-update').textContent = timestamp;
}

// 开始自动刷新
function startAutoRefresh() {
    autoRefreshInterval = setInterval(loadStatus, 30000); // 30秒刷新一次
}

// 停止自动刷新
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
}

// 手动清理
async function runCleanup() {
    if (!confirm(t('confirmCleanup'))) {
        return;
    }
    
    try {
        const response = await fetch('/api/cleanup/run', {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            alert(t('cleanupComplete') + '\n' + JSON.stringify(result.results, null, 2));
            loadStatus(); // 重新加载状态
        } else {
            alert(t('cleanupFailed') + ': ' + result.error);
        }
    } catch (error) {
        alert(t('requestFailed') + ': ' + error.message);
    }
}

// 显示缓存统计
async function showCacheStats() {
    try {
        const response = await fetch('/api/cache/stats');
        const result = await response.json();
        
        if (result.success) {
            const stats = result.data;
            alert(t('cacheStatsTitle') + '\n\n' +
                  t('memoryCache') + ': ' + stats.memory_size + ' ' + t('items') + '\n' +
                  t('dbCache') + ': ' + (stats.db_size || 0) + ' ' + t('items') + '\n' +
                  t('cacheExpiry') + ': ' + stats.ttl_minutes + ' ' + t('minutes') + '\n' +
                  t('maxCapacity') + ': ' + stats.max_size + ' ' + t('items'));
        } else {
            alert(t('requestFailed') + ': ' + result.error);
        }
    } catch (error) {
        alert(t('requestFailed') + ': ' + error.message);
    }
}

// 显示清理状态
async function showCleanupStatus() {
    try {
        const response = await fetch('/api/cleanup/status');
        const result = await response.json();
        
        if (result.success) {
            const status = result.data;
            alert(t('cleanupStatusTitle') + '\n\n' +
                  t('runningStatus') + ': ' + (status.running ? t('running') : t('stopped')) + '\n' +
                  t('elapsed') + ': ' + status.elapsed_minutes + ' ' + t('minutes') + '\n' +
                  t('remaining') + ': ' + status.remaining_minutes + ' ' + t('minutes') + '\n' +
                  t('cleanupCount') + ': ' + status.session_cleanups + ' ' + t('times') + '\n' +
                  t('cleanedItems') + ': ' + status.total_items_cleaned + ' ' + t('items'));
        } else {
            alert(t('requestFailed') + ': ' + result.error);
        }
    } catch (error) {
        alert(t('requestFailed') + ': ' + error.message);
    }
}

// 健康检查
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const result = await response.json();
        
        let message = t('healthCheckTitle') + '\n\n' +
                     t('status') + ': ' + result.status + '\n' +
                     t('service') + ': ' + result.service + '\n' +
                     t('time') + ': ' + result.timestamp + '\n' +
                     t('cacheStatus') + ': ' + result.cache_size + ' ' + t('items') + '\n\n' +
                     t('featuresStatus') + ':\n';
        
        for (const [key, value] of Object.entries(result.features)) {
            message += `  ${key}: ${value ? '✓' : '✗'}\n`;
        }
        
        if (result.performance) {
            message += '\n' + t('performance') + ':\n' +
                      '  ' + t('avgResponseTime') + ': ' + result.performance.avg_response_time_ms + 'ms\n' +
                      '  ' + t('totalRequests') + ': ' + result.performance.total_requests + '\n' +
                      '  ' + t('cacheHitRate') + ': ' + result.performance.cache_hit_rate + '%';
        }
        
        alert(message);
    } catch (error) {
        alert(t('requestFailed') + ': ' + error.message);
    }
}

// 关闭服务器
async function shutdownServer() {
    if (!confirm(t('confirmShutdown'))) {
        return;
    }
    
    try {
        const response = await fetch('/api/shutdown', {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            alert(t('shuttingDown'));
            stopAutoRefresh();
        } else {
            alert(t('shutdownFailed') + ': ' + result.error);
        }
    } catch (error) {
        console.log(t('shuttingDown'));
    }
}

// 页面卸载时停止自动刷新
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});