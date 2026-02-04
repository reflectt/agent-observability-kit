// Trace detail viewer

let currentTrace = null;

async function loadTrace() {
    try {
        const response = await fetch(`/api/trace/${TRACE_ID}`);
        currentTrace = await response.json();
        
        if (currentTrace.error) {
            document.getElementById('trace-metadata').innerHTML = `
                <div class="error-message">${currentTrace.error}</div>
            `;
            return;
        }
        
        renderTraceMetadata();
        renderExecutionGraph();
        renderSpanList();
        
    } catch (error) {
        document.getElementById('trace-metadata').innerHTML = `
            <div class="error-message">Error loading trace: ${error.message}</div>
        `;
    }
}

function renderTraceMetadata() {
    document.getElementById('trace-title').textContent = currentTrace.name || 'Trace';
    document.getElementById('trace-id').textContent = currentTrace.trace_id;
    
    const metadata = currentTrace.metadata || {};
    const firstSpan = currentTrace.spans[0] || {};
    const lastSpan = currentTrace.spans[currentTrace.spans.length - 1] || {};
    
    document.getElementById('trace-metadata').innerHTML = `
        <div class="metadata-grid">
            <div class="metadata-item">
                <div class="metadata-label">Status</div>
                <div class="metadata-value">
                    <span class="trace-status ${currentTrace.spans.some(s => s.status === 'error') ? 'error' : 'success'}">
                        ${currentTrace.spans.some(s => s.status === 'error') ? 'Error' : 'Success'}
                    </span>
                </div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Total Duration</div>
                <div class="metadata-value">${(metadata.total_duration_ms || 0).toFixed(0)}ms</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Span Count</div>
                <div class="metadata-value">${metadata.span_count || 0}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Start Time</div>
                <div class="metadata-value">${new Date(firstSpan.start_time).toLocaleString()}</div>
            </div>
            ${metadata.agent_id ? `
            <div class="metadata-item">
                <div class="metadata-label">Agent</div>
                <div class="metadata-value">${metadata.agent_id}</div>
            </div>
            ` : ''}
            ${metadata.framework ? `
            <div class="metadata-item">
                <div class="metadata-label">Framework</div>
                <div class="metadata-value">${metadata.framework}</div>
            </div>
            ` : ''}
        </div>
    `;
}

function renderExecutionGraph() {
    const graph = document.getElementById('execution-graph');
    
    // Build span tree
    const spanMap = new Map();
    currentTrace.spans.forEach(span => spanMap.set(span.span_id, span));
    
    const rootSpans = currentTrace.spans.filter(s => !s.parent_span_id);
    
    function renderSpanNode(span, depth = 0) {
        const indent = depth > 0 ? 'span-indent' : '';
        const statusClass = span.status === 'error' ? 'error' : 'success';
        const icon = span.status === 'error' ? '🔴' : '🟢';
        
        return `
            <div class="span-node ${statusClass} ${indent}" onclick="showSpanDetail('${span.span_id}')">
                <div class="span-header">
                    <div>
                        <span>${icon}</span>
                        <span class="span-name">${span.name}</span>
                        <span class="span-type">(${span.span_type})</span>
                    </div>
                    <div class="span-meta">
                        <span>⏱️ ${(span.duration_ms || 0).toFixed(0)}ms</span>
                        ${span.llm_calls.length > 0 ? `<span>🤖 ${span.llm_calls.length} LLM calls</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Render all spans (simplified view - no nested rendering for MVP)
    graph.innerHTML = currentTrace.spans
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
        .map(span => renderSpanNode(span))
        .join('');
}

function renderSpanList() {
    const list = document.getElementById('span-list');
    
    list.innerHTML = currentTrace.spans
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
        .map(span => {
            const statusClass = span.status === 'error' ? 'error' : 'success';
            return `
                <div class="span-node ${statusClass}" onclick="showSpanDetail('${span.span_id}')">
                    <div class="span-header">
                        <div>
                            <span class="span-name">${span.name}</span>
                            <span class="span-type">(${span.span_type})</span>
                        </div>
                        <div class="span-meta">
                            <span>⏱️ ${(span.duration_ms || 0).toFixed(0)}ms</span>
                            <span>🕐 ${new Date(span.start_time).toLocaleTimeString()}</span>
                        </div>
                    </div>
                </div>
            `;
        })
        .join('');
}

function showSpanDetail(spanId) {
    const span = currentTrace.spans.find(s => s.span_id === spanId);
    if (!span) return;
    
    const modal = document.getElementById('span-modal');
    const content = document.getElementById('span-detail-content');
    
    const llmCallsHtml = span.llm_calls.length > 0 ? `
        <div class="detail-section">
            <h3>🤖 LLM Calls (${span.llm_calls.length})</h3>
            ${span.llm_calls.map((call, idx) => `
                <div class="json-view" style="margin-bottom: 1rem;">
                    <strong>Call ${idx + 1}: ${call.model}</strong><br>
                    <strong>Latency:</strong> ${call.latency_ms.toFixed(0)}ms<br>
                    <strong>Tokens:</strong> ${JSON.stringify(call.tokens)}<br>
                    ${call.cost ? `<strong>Cost:</strong> $${call.cost.toFixed(4)}<br>` : ''}
                    <br>
                    <strong>Prompt:</strong><br>
                    <pre>${call.prompt}</pre>
                    <br>
                    <strong>Response:</strong><br>
                    <pre>${call.response}</pre>
                </div>
            `).join('')}
        </div>
    ` : '';
    
    content.innerHTML = `
        <h2>${span.name}</h2>
        <p><strong>Span ID:</strong> ${span.span_id}</p>
        <p><strong>Type:</strong> ${span.span_type}</p>
        <p><strong>Status:</strong> <span class="trace-status ${span.status}">${span.status}</span></p>
        <p><strong>Duration:</strong> ${(span.duration_ms || 0).toFixed(2)}ms</p>
        
        <div class="detail-section">
            <h3>📥 Inputs</h3>
            <div class="json-view">
                <pre>${JSON.stringify(span.inputs, null, 2)}</pre>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>📤 Outputs</h3>
            <div class="json-view">
                <pre>${JSON.stringify(span.outputs, null, 2)}</pre>
            </div>
        </div>
        
        ${llmCallsHtml}
        
        ${span.error ? `
        <div class="detail-section">
            <h3>❌ Error</h3>
            <div class="error-message">
                <strong>${span.error_type}</strong><br>
                ${span.error}
            </div>
        </div>
        ` : ''}
        
        <div class="detail-section">
            <h3>📋 Metadata</h3>
            <div class="json-view">
                <pre>${JSON.stringify(span.metadata, null, 2)}</pre>
            </div>
        </div>
    `;
    
    modal.classList.add('active');
}

// Close modal
document.querySelector('.close').onclick = function() {
    document.getElementById('span-modal').classList.remove('active');
};

window.onclick = function(event) {
    const modal = document.getElementById('span-modal');
    if (event.target == modal) {
        modal.classList.remove('active');
    }
};

loadTrace();
