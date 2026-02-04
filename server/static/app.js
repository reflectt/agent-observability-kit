// Main trace list page

async function loadTraces() {
    try {
        const response = await fetch('/api/traces');
        const traces = await response.json();
        
        if (traces.length === 0) {
            document.getElementById('trace-list').innerHTML = `
                <div class="loading">
                    No traces yet. Run an example to generate traces!
                </div>
            `;
            return;
        }
        
        // Update stats
        const totalTraces = traces.length;
        const successfulTraces = traces.filter(t => t.status === 'success').length;
        const successRate = (successfulTraces / totalTraces * 100).toFixed(1);
        const avgDuration = (traces.reduce((sum, t) => sum + (t.total_duration_ms || 0), 0) / totalTraces).toFixed(0);
        const totalSpans = traces.reduce((sum, t) => sum + (t.span_count || 0), 0);
        
        document.getElementById('total-traces').textContent = totalTraces;
        document.getElementById('success-rate').textContent = `${successRate}%`;
        document.getElementById('avg-duration').textContent = `${avgDuration}ms`;
        document.getElementById('total-spans').textContent = totalSpans;
        
        // Render trace list
        const traceList = document.getElementById('trace-list');
        traceList.innerHTML = traces.map(trace => `
            <div class="trace-item" onclick="window.location.href='/trace/${trace.trace_id}'">
                <div class="trace-header">
                    <span class="trace-name">${trace.name || 'Unnamed trace'}</span>
                    <span class="trace-status ${trace.status}">${trace.status}</span>
                </div>
                <div class="trace-meta">
                    <span>📊 ${trace.span_count || 0} spans</span>
                    <span>⏱️ ${(trace.total_duration_ms || 0).toFixed(0)}ms</span>
                    <span>🕐 ${new Date(trace.start_time).toLocaleString()}</span>
                    ${trace.agent_id ? `<span>🤖 ${trace.agent_id}</span>` : ''}
                    ${trace.framework ? `<span>🔧 ${trace.framework}</span>` : ''}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        document.getElementById('trace-list').innerHTML = `
            <div class="error-message">
                Error loading traces: ${error.message}
            </div>
        `;
    }
}

// Auto-refresh every 5 seconds
loadTraces();
setInterval(loadTraces, 5000);
