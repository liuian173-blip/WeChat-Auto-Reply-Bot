// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    setInterval(loadDashboard, 30000); // 30秒刷新一次
});

async function loadDashboard() {
    await Promise.all([
        loadStats(),
        loadSlowRequests(),
        loadBottlenecks()
    ]);
}

// 加载统计数据
async function loadStats() {
    try {
        const response = await fetch('/api/performance/stats?hours=24');
        const result = await response.json();
        
        if (result.success) {
            updateMetrics(result.data);
            updateTypeStats(result.data.by_type);
            document.getElementById('last-update').textContent = result.timestamp;
        }
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 更新核心指标
function updateMetrics(stats) {
    const metricsDiv = document.getElementById('metrics');
    const avgResponse = stats.avg_response_time_ms || 0;
    
    let avgClass = '';
    if (avgResponse < 3000) avgClass = 'success';
    else if (avgResponse < 4500) avgClass = 'warning';
    
    let slowClass = (stats.slow_requests || 0) > 0 ? 'warning' : 'success';
    let timeoutClass = (stats.timeout_requests || 0) > 0 ? 'warning' : 'success';
    
    metricsDiv.innerHTML = `
        <div class="metric ${avgClass}">
            <div class="metric-value">${avgResponse}ms</div>
            <div class="metric-label" data-i18n="avgResponseTime">${t('avgResponseTime')}</div>
        </div>
        <div class="metric">
            <div class="metric-value">${stats.total_requests || 0}</div>
            <div class="metric-label" data-i18n="totalRequests">${t('totalRequests')}</div>
        </div>
        <div class="metric success">
            <div class="metric-value">${stats.cache_hit_rate || 0}%</div>
            <div class="metric-label" data-i18n="cacheHitRate">${t('cacheHitRate')}</div>
        </div>
        <div class="metric ${slowClass}">
            <div class="metric-value">${stats.slow_requests || 0}</div>
            <div class="metric-label" data-i18n="slowRequests">${t('slowRequests')} (>3s)</div>
        </div>
        <div class="metric ${timeoutClass}">
            <div class="metric-value">${stats.timeout_requests || 0}</div>
            <div class="metric-label" data-i18n="timeoutRequests">${t('timeoutRequests')}</div>
        </div>
    `;
}

// 更新类型统计
function updateTypeStats(byType) {
    const tbody = document.querySelector('#type-stats tbody');
    
    if (!byType || Object.keys(byType).length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #999;" data-i18n="noData">${t('noData')}</td></tr>`;
        return;
    }
    
    let html = '';
    for (const [type, data] of Object.entries(byType)) {
        const avgClass = data.avg_time_ms < 3000 ? 'status-success' : 
                        data.avg_time_ms < 4500 ? 'status-warning' : 'status-error';
        const maxClass = data.max_time_ms < 3000 ? 'status-success' : 
                        data.max_time_ms < 4500 ? 'status-warning' : 'status-error';
        
        html += `
            <tr>
                <td>${type}</td>
                <td>${data.count}</td>
                <td class="${avgClass}">${data.avg_time_ms}ms</td>
                <td class="${maxClass}">${data.max_time_ms}ms</td>
            </tr>
        `;
    }
    
    tbody.innerHTML = html;
}

// 加载慢请求
async function loadSlowRequests() {
    try {
        const response = await fetch('/api/performance/slow?limit=5');
        const result = await response.json();
        
        if (result.success) {
            updateSlowRequests(result.data);
        }
    } catch (error) {
        console.error('加载慢请求失败:', error);
    }
}

// 更新慢请求表格
function updateSlowRequests(requests) {
    const tbody = document.querySelector('#slow-requests tbody');
    
    if (!requests || requests.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #999;" data-i18n="noData">${t('noData')}</td></tr>`;
        return;
    }
    
    let html = '';
    for (const req of requests) {
        const statusClass = req.status === 'success' ? 'status-success' : 'status-error';
        const statusText = req.status === 'success' ? t('success') : t('failed');
        
        html += `
            <tr>
                <td>${req.type}</td>
                <td>${req.user_id}</td>
                <td class="status-error">${req.duration_ms}ms</td>
                <td class="${statusClass}">${statusText}</td>
                <td>${req.time}</td>
            </tr>
        `;
    }
    
    tbody.innerHTML = html;
}

// 加载瓶颈分析
async function loadBottlenecks() {
    try {
        const response = await fetch('/api/performance/bottlenecks');
        const result = await response.json();
        
        if (result.success) {
            updateBottlenecks(result.data.slice(0, 5));
        }
    } catch (error) {
        console.error('加载瓶颈分析失败:', error);
    }
}

// 更新瓶颈表格
function updateBottlenecks(bottlenecks) {
    const tbody = document.querySelector('#bottlenecks tbody');
    
    if (!bottlenecks || bottlenecks.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #999;" data-i18n="noData">${t('noData')}</td></tr>`;
        return;
    }
    
    let html = '';
    for (const bn of bottlenecks) {
        const timeClass = bn.avg_time_ms < 1000 ? 'status-success' : 
                         bn.avg_time_ms < 2000 ? 'status-warning' : 'status-error';
        
        html += `
            <tr>
                <td>${bn.component}</td>
                <td>${bn.operation}</td>
                <td class="${timeClass}">${bn.avg_time_ms}ms</td>
                <td>${bn.count}</td>
            </tr>
        `;
    }
    
    tbody.innerHTML = html;
}