class SIEMSpeakApp {
    constructor() {
        this.currentCharts = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadConversationHistory();
    }

    bindEvents() {
        // Chat form submission
        document.getElementById('chatForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendQuestion();
        });

        // Example questions
        document.querySelectorAll('.example-question').forEach(button => {
            button.addEventListener('click', (e) => {
                const question = e.currentTarget.getAttribute('data-question');
                document.getElementById('questionInput').value = question;
                this.sendQuestion(question);
            });
        });

        // Clear chat
        document.getElementById('clearChat').addEventListener('click', () => {
            this.clearConversation();
        });

        // Enter key to send
        document.getElementById('questionInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendQuestion();
            }
        });
    }

    async sendQuestion(question = null) {
        const input = document.getElementById('questionInput');
        const questionText = question || input.value.trim();

        if (!questionText) return;

        // Clear input
        if (!question) input.value = '';

        // Add user message to chat
        this.addMessage(questionText, 'user');

        // Show loading indicator
        this.showLoading();

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: questionText })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Unknown error');
            }

            // Add bot response
            this.addBotResponse(data);

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'bot', true);
        } finally {
            this.hideLoading();
            this.scrollToBottom();
        }
    }

    addMessage(text, type, isError = false) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        
        messageDiv.className = `message ${type}-message p-3 mb-2`;
        if (isError) messageDiv.classList.add('bg-danger', 'text-white');

        messageDiv.style.maxWidth = '70%';
        messageDiv.innerHTML = `
            <div class="d-flex align-items-center mb-1">
                <small class="fw-bold">${type === 'user' ? 'You' : 'SIEM Assistant'}</small>
                <small class="ms-2 text-muted">${new Date().toLocaleTimeString()}</small>
            </div>
            <div>${this.escapeHtml(text)}</div>
        `;

        // Remove welcome message if it exists
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) welcomeMsg.remove();

        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addBotResponse(data) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        
        messageDiv.className = 'message bot-message p-3 mb-2';
        messageDiv.style.maxWidth = '85%';

        const { reply, generated_query, entities } = data;

        let content = `
            <div class="d-flex align-items-center mb-2">
                <small class="fw-bold">SIEM Assistant</small>
                <small class="ms-2 text-muted">${new Date().toLocaleTimeString()}</small>
            </div>
            
            <div class="results-summary p-2 mb-2 rounded">
                <i class="fas fa-chart-bar me-2"></i>
                ${reply.summary}
            </div>

            <div class="query-preview p-2 mb-2 rounded">
                <small><strong>Generated Query:</strong></small>
                <pre class="mb-0 mt-1"><code>${JSON.stringify(generated_query, null, 2)}</code></pre>
            </div>
        `;

        // Add charts if available
        if (reply.chart_data && Object.keys(reply.chart_data).length > 0) {
            content += `<div class="charts-container mb-2">`;
            
            Object.keys(reply.chart_data).forEach(chartType => {
                const chartId = `chart-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                content += `
                    <div class="chart-wrapper mb-3">
                        <div class="chart-container">
                            <canvas id="${chartId}"></canvas>
                        </div>
                    </div>
                `;
            });
            
            content += `</div>`;
        }

        // Add table preview
        if (reply.table_data && reply.table_data.length > 0) {
            const sampleRows = reply.table_data.slice(0, 3);
            content += `
                <div class="table-preview mb-2">
                    <small><strong>Sample Results (${reply.table_data.length} total):</strong></small>
                    <div class="table-responsive mt-1">
                        <table class="table table-sm table-striped">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Source IP</th>
                                    <th>Action</th>
                                    <th>User</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${sampleRows.map(row => `
                                    <tr>
                                        <td>${new Date(row.timestamp).toLocaleTimeString()}</td>
                                        <td>${row.source_ip}</td>
                                        <td>${row.event_action}</td>
                                        <td>${row.user}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${reply.table_data.length > 3 ? 
                        `<button class="btn btn-outline-primary btn-sm w-100 view-full-results" 
                                data-results='${JSON.stringify(reply)}'>
                            <i class="fas fa-external-link-alt me-1"></i>
                            View Full Results (${reply.table_data.length} events)
                        </button>` : ''}
                </div>
            `;
        }

        messageDiv.innerHTML = content;
        chatMessages.appendChild(messageDiv);

        // Render charts
        this.renderCharts(reply.chart_data, messageDiv);

        // Bind view full results buttons
        messageDiv.querySelectorAll('.view-full-results').forEach(button => {
            button.addEventListener('click', (e) => {
                const results = JSON.parse(e.currentTarget.getAttribute('data-results'));
                this.showFullResults(results, generated_query);
            });
        });

        this.scrollToBottom();
    }

    renderCharts(chartData, container) {
        if (!chartData) return;

        Object.keys(chartData).forEach((chartType, index) => {
            const chartId = container.querySelectorAll('.chart-container canvas')[index]?.id;
            if (!chartId) return;

            const ctx = document.getElementById(chartId).getContext('2d');
            const data = chartData[chartType];

            let chartConfig = {};

            switch(chartType) {
                case 'timeline':
                    chartConfig = {
                        type: 'line',
                        data: {
                            labels: data.labels.map(label => new Date(label).toLocaleTimeString()),
                            datasets: [{
                                label: 'Events Timeline',
                                data: data.values,
                                borderColor: '#007bff',
                                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                                tension: 0.4,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false }
                            },
                            scales: {
                                x: { 
                                    display: true,
                                    title: { display: true, text: 'Time' }
                                },
                                y: { 
                                    display: true,
                                    title: { display: true, text: 'Event Count' },
                                    beginAtZero: true
                                }
                            }
                        }
                    };
                    break;

                case 'top_ips':
                    chartConfig = {
                        type: 'bar',
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: 'Event Count',
                                data: data.values,
                                backgroundColor: '#28a745'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false }
                            },
                            scales: {
                                x: { 
                                    display: true,
                                    title: { display: true, text: 'Source IP' }
                                },
                                y: { 
                                    display: true,
                                    title: { display: true, text: 'Event Count' },
                                    beginAtZero: true
                                }
                            }
                        }
                    };
                    break;
            }

            if (chartConfig.type) {
                const chart = new Chart(ctx, chartConfig);
                this.currentCharts.push(chart);
            }
        });
    }

    showFullResults(results, generatedQuery) {
        const modalBody = document.getElementById('modalBody');
        
        let content = `
            <div class="row">
                <div class="col-12">
                    <div class="card mb-3">
                        <div class="card-header">
                            <h6 class="mb-0">Generated Query</h6>
                        </div>
                        <div class="card-body">
                            <pre class="mb-0"><code>${JSON.stringify(generatedQuery, null, 2)}</code></pre>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Results (${results.total_hits} events)</h6>
                        </div>
                        <div class="card-body">
        `;

        // Add charts
        if (results.chart_data && Object.keys(results.chart_data).length > 0) {
            content += `<div class="row mb-4">`;
            Object.keys(results.chart_data).forEach(chartType => {
                const chartId = `modal-chart-${chartType}`;
                content += `
                    <div class="col-md-6">
                        <div class="chart-container" style="height: 250px;">
                            <canvas id="${chartId}"></canvas>
                        </div>
                    </div>
                `;
            });
            content += `</div>`;
        }

        // Add full table
        content += `
                            <div class="table-responsive">
                                <table class="table table-striped table-hover">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>Timestamp</th>
                                            <th>Source IP</th>
                                            <th>Event Action</th>
                                            <th>User</th>
                                            <th>Message</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${results.table_data.map(row => `
                                            <tr>
                                                <td>${new Date(row.timestamp).toLocaleString()}</td>
                                                <td><code>${row.source_ip}</code></td>
                                                <td><span class="badge bg-secondary">${row.event_action}</span></td>
                                                <td>${row.user}</td>
                                                <td><small>${this.escapeHtml(row.message || '')}</small></td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        modalBody.innerHTML = content;

        // Render modal charts
        if (results.chart_data) {
            setTimeout(() => {
                Object.keys(results.chart_data).forEach(chartType => {
                    const chartId = `modal-chart-${chartType}`;
                    const ctx = document.getElementById(chartId)?.getContext('2d');
                    if (ctx) {
                        // Similar chart rendering logic as above
                        this.renderModalChart(chartType, results.chart_data[chartType], ctx);
                    }
                });
            }, 100);
        }

        const resultsModal = new bootstrap.Modal(document.getElementById('resultsModal'));
        resultsModal.show();
    }

    renderModalChart(chartType, data, ctx) {
        // Simplified chart rendering for modal
        const configs = {
            timeline: { type: 'line', color: '#007bff' },
            top_ips: { type: 'bar', color: '#28a745' }
        };

        const config = configs[chartType];
        if (!config) return;

        new Chart(ctx, {
            type: config.type,
            data: {
                labels: data.labels.map(label => 
                    chartType === 'timeline' ? new Date(label).toLocaleTimeString() : label
                ),
                datasets: [{
                    label: chartType === 'timeline' ? 'Events' : 'Count',
                    data: data.values,
                    backgroundColor: config.color,
                    borderColor: config.type === 'line' ? config.color : undefined,
                    fill: config.type === 'line'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    showLoading() {
        document.getElementById('loadingIndicator').style.display = 'block';
        document.getElementById('questionInput').disabled = true;
    }

    hideLoading() {
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('questionInput').disabled = false;
        document.getElementById('questionInput').focus();
    }

    async loadConversationHistory() {
        try {
            const response = await fetch('/conversation');
            const data = await response.json();
            
            if (data.conversation && data.conversation.length > 0) {
                // Clear welcome message
                const welcomeMsg = document.getElementById('chatMessages').querySelector('.welcome-message');
                if (welcomeMsg) welcomeMsg.remove();

                // Replay conversation
                data.conversation.forEach(entry => {
                    this.addMessage(entry.question, 'user');
                    // For simplicity, we'll just show the summary in replay
                    this.addMessage(entry.results.summary, 'bot');
                });
            }
        } catch (error) {
            console.error('Failed to load conversation history:', error);
        }
    }

    async clearConversation() {
        if (!confirm('Are you sure you want to clear the conversation?')) return;

        try {
            await fetch('/clear', { method: 'POST' });
            document.getElementById('chatMessages').innerHTML = `
                <div class="welcome-message text-center text-muted">
                    <i class="fas fa-robot fa-3x mb-3"></i>
                    <h5>Welcome to SIEMSpeak</h5>
                    <p>Ask me questions about your security data in plain English</p>
                </div>
            `;
            
            // Clear any current charts
            this.currentCharts.forEach(chart => chart.destroy());
            this.currentCharts = [];
        } catch (error) {
            console.error('Failed to clear conversation:', error);
        }
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SIEMSpeakApp();
});