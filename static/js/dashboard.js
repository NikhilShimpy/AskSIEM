// Dashboard-specific JavaScript for SIEMSpeak

class SIEMSpeakDashboard {
    constructor() {
        this.currentResults = null;
        this.isLoading = false;
        this.currentCharts = [];
        this.conversationHistory = [];
        this.currentFilters = {};
    }

    init() {
        this.bindDashboardEvents();
        this.initializeFilters();
        this.updateOverviewCards();
        
        // Add event delegation for dynamic elements
        this.setupEventDelegation();
    }

    setupEventDelegation() {
        // Event delegation for dynamically created elements
        document.addEventListener('click', (e) => {
            // Example queries
            if (e.target.closest('.example-query')) {
                const button = e.target.closest('.example-query');
                const query = button.getAttribute('data-query');
                this.sendQuestion(query);
            }

            // View all charts
            if (e.target.closest('.view-all-charts')) {
                const button = e.target.closest('.view-all-charts');
                const results = JSON.parse(button.getAttribute('data-results'));
                this.showFullResults(results);
            }

            // Export results
            if (e.target.closest('.export-results')) {
                const button = e.target.closest('.export-results');
                const results = JSON.parse(button.getAttribute('data-results'));
                this.exportResultsAsCSV(results);
            }

            // View details
            if (e.target.closest('.view-details')) {
                const button = e.target.closest('.view-details');
                const results = JSON.parse(button.getAttribute('data-results'));
                this.showDetailedAnalysis(results);
            }

            // Refine search
            if (e.target.closest('.refine-search')) {
                const button = e.target.closest('.refine-search');
                const question = button.getAttribute('data-question');
                const input = document.getElementById('questionInput');
                if (input) {
                    input.value = question;
                    input.focus();
                }
            }

            // Chart controls
            if (e.target.closest('.chart-export')) {
                const button = e.target.closest('.chart-export');
                const chartId = button.getAttribute('data-chart-id');
                this.exportChart(chartId);
            }

            if (e.target.closest('.chart-fullscreen')) {
                const button = e.target.closest('.chart-fullscreen');
                const chartId = button.getAttribute('data-chart-id');
                this.toggleFullscreenChart(chartId);
            }

            // Clear chat
            if (e.target.closest('#clearChat')) {
                this.clearChat();
            }

            // Export results button
            if (e.target.closest('#exportResults')) {
                this.exportCurrentResults();
            }
        });
    }

    bindDashboardEvents() {
        // Chat form submission
        const chatForm = document.getElementById('chatForm');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendQuestion();
            });
        }

        // Filter application
        const applyFiltersBtn = document.getElementById('applyFilters');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => {
                this.applyAdvancedFilters();
            });
        }

        // Filter reset
        const resetFiltersBtn = document.getElementById('resetFilters');
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }

        // Enter key support
        const questionInput = document.getElementById('questionInput');
        if (questionInput) {
            questionInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendQuestion();
                }
            });

            // Autocomplete
            questionInput.addEventListener('input', this.debounce(() => {
                this.handleAutocomplete(questionInput.value);
            }, 300));
        }

        // Real-time filter updates
        const filterIds = ['timeFilter', 'severityFilter', 'eventTypeFilter', 'statusFilter', 
                          'countryFilter', 'riskScoreFilter'];
        
        filterIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    this.updateActiveFilters();
                });
            }
        });

        const inputFilterIds = ['sourceIpFilter', 'userFilter', 'keywordFilter'];
        inputFilterIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', this.debounce(() => {
                    this.updateActiveFilters();
                }, 500));
            }
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    initializeFilters() {
        // Set default time filter to 24 hours
        this.currentFilters = {
            time_range: { unit: 'hours', value: 24, type: 'relative' }
        };
        this.updateFilterDisplay();
    }

    updateActiveFilters() {
        const filters = {
            time_range: this.getTimeFilter(),
            severity: document.getElementById('severityFilter')?.value || null,
            event_type: document.getElementById('eventTypeFilter')?.value || null,
            status: document.getElementById('statusFilter')?.value || null,
            source_ip: document.getElementById('sourceIpFilter')?.value || null,
            user: document.getElementById('userFilter')?.value || null,
            country: document.getElementById('countryFilter')?.value || null,
            risk_score: this.getRiskScoreRange(),
            keywords: document.getElementById('keywordFilter')?.value ? 
                     [document.getElementById('keywordFilter').value] : []
        };

        // Remove null values
        Object.keys(filters).forEach(key => {
            if (filters[key] === null || (Array.isArray(filters[key]) && filters[key].length === 0)) {
                delete filters[key];
            }
        });

        this.currentFilters = filters;
        this.updateFilterDisplay();
    }

    getTimeFilter() {
        const timeValue = document.getElementById('timeFilter')?.value;
        const timeMap = {
            '1h': { unit: 'hours', value: 1, type: 'relative' },
            '24h': { unit: 'hours', value: 24, type: 'relative' },
            '7d': { unit: 'days', value: 7, type: 'relative' },
            '30d': { unit: 'days', value: 30, type: 'relative' }
        };
        return timeMap[timeValue] || timeMap['24h'];
    }

    getRiskScoreRange() {
        const riskValue = document.getElementById('riskScoreFilter')?.value;
        const riskMap = {
            'high': [70, 100],
            'medium': [40, 69],
            'low': [0, 39]
        };
        return riskMap[riskValue] || null;
    }

    updateFilterDisplay() {
        const applyButton = document.getElementById('applyFilters');
        if (!applyButton) return;

        const filterCount = Object.keys(this.currentFilters).length;
        
        if (filterCount > 1) {
            applyButton.innerHTML = `<i class="fas fa-filter me-1"></i> Apply (${filterCount})`;
            applyButton.classList.remove('btn-outline-primary');
            applyButton.classList.add('btn-primary');
        } else {
            applyButton.innerHTML = `<i class="fas fa-filter me-1"></i> Apply Filters`;
            applyButton.classList.remove('btn-primary');
            applyButton.classList.add('btn-outline-primary');
        }
    }

    resetFilters() {
        // Reset all filter inputs to default
        const filterIds = ['timeFilter', 'severityFilter', 'eventTypeFilter', 'statusFilter', 
                          'sourceIpFilter', 'userFilter', 'countryFilter', 'keywordFilter', 'riskScoreFilter'];
        
        filterIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                if (element.tagName === 'SELECT') {
                    element.selectedIndex = 0;
                } else {
                    element.value = '';
                }
            }
        });

        // Reset current filters
        this.currentFilters = {
            time_range: { unit: 'hours', value: 24, type: 'relative' }
        };
        
        this.updateFilterDisplay();
    }

    async applyAdvancedFilters() {
        this.showLoading();
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filters: this.currentFilters })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Filtering failed');
            }

            this.displayFilterResults(data);
            
        } catch (error) {
            this.showError(`Filter error: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    displayFilterResults(data) {
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection) return;

        resultsSection.innerHTML = this.createFilterResultsHTML(data);
        this.showExportButton();
    }

    createFilterResultsHTML(data) {
        return `
            <div class="card bg-darker border-0 shadow mt-4">
                <div class="card-header bg-gradient-dark border-0">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-0">
                                <i class="fas fa-filter text-primary me-2"></i>
                                Filter Results
                            </h6>
                            <small class="text-muted">${data.total_count} events found</small>
                        </div>
                        <button class="btn btn-sm btn-outline-success export-filtered" 
                                data-events='${JSON.stringify(data.events)}'>
                            <i class="fas fa-download me-1"></i> Export CSV
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    ${this.createEventsTable(data.events)}
                </div>
            </div>
        `;
    }

    createEventsTable(events) {
        if (!events || events.length === 0) {
            return '<p class="text-muted text-center py-4">No events found matching your filters.</p>';
        }

        return `
            <div class="table-responsive">
                <table class="table table-dark table-striped table-hover events-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Event Type</th>
                            <th>Source IP</th>
                            <th>User</th>
                            <th>Severity</th>
                            <th>Country</th>
                            <th>Risk Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${events.map(event => `
                            <tr>
                                <td>${this.formatDate(event.timestamp)}</td>
                                <td>
                                    <span class="badge bg-secondary text-capitalize">
                                        ${event.event_type.replace('_', ' ')}
                                    </span>
                                </td>
                                <td><code class="text-info">${event.source_ip}</code></td>
                                <td>${event.user}</td>
                                <td>
                                    <span class="badge ${this.getSeverityBadgeClass(event.severity)}">
                                        ${event.severity}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge bg-dark">
                                        <i class="fas fa-globe me-1"></i>${event.country}
                                    </span>
                                </td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="progress flex-grow-1 me-2" style="height: 6px;">
                                            <div class="progress-bar ${this.getRiskScoreClass(event.risk_score)}" 
                                                 style="width: ${event.risk_score}%"></div>
                                        </div>
                                        <small>${event.risk_score}</small>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    async sendQuestion(question = null) {
        if (this.isLoading) return;

        const input = document.getElementById('questionInput');
        const questionText = question || input?.value.trim();

        if (!questionText) return;

        // Clear input if not from example
        if (!question && input) {
            input.value = '';
        }

        // Add user message to chat
        this.addMessage(questionText, 'user');

        // Show loading indicator
        this.showLoading();

        this.isLoading = true;

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: questionText })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Unknown error');
            }

            // Add bot response with enhanced formatting
            this.addAdvancedBotResponse(data, questionText);
            
            // Store in conversation history
            this.conversationHistory.push({
                question: questionText,
                response: data,
                timestamp: new Date().toISOString()
            });

            // Display results
            this.displayQueryResults(data);

        } catch (error) {
            this.addMessage(`Error: ${error.message}`, 'bot', true);
            console.error('Query error:', error);
        } finally {
            this.hideLoading();
            this.scrollToBottom();
            this.isLoading = false;
        }
    }

    addAdvancedBotResponse(data, originalQuestion) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message advanced-response';
        messageDiv.innerHTML = this.formatAdvancedResponse(data, originalQuestion);

        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Remove welcome message if it exists
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        // Initialize preview charts after a short delay
        setTimeout(() => {
            this.initializePreviewCharts(data.results.chart_data, messageDiv);
        }, 100);
    }

    formatAdvancedResponse(data, question) {
        const { results, parsed_query, processing_time } = data;
        
        return `
            <div class="response-header mb-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong class="text-primary">SIEM Assistant</strong>
                        <small class="text-muted ms-2">${new Date().toLocaleTimeString()}</small>
                    </div>
                    <div class="response-meta">
                        <small class="text-muted">Processed in ${processing_time}</small>
                    </div>
                </div>
            </div>

            <!-- Summary Card -->
            <div class="summary-card alert alert-info border-0 mb-3">
                <div class="d-flex align-items-center">
                    <i class="fas fa-chart-line me-3 fa-lg"></i>
                    <div class="flex-grow-1">
                        <h6 class="mb-1">Analysis Summary</h6>
                        <p class="mb-0">${results.summary}</p>
                    </div>
                    <div class="badge bg-primary fs-6">${results.total_events} events</div>
                </div>
            </div>

            <!-- Insights -->
            ${results.insights && results.insights.length > 0 ? `
                <div class="insights-section mb-3">
                    <h6 class="text-warning mb-2">
                        <i class="fas fa-lightbulb me-1"></i> Key Insights
                    </h6>
                    <div class="row g-2">
                        ${results.insights.map(insight => `
                            <div class="col-md-6">
                                <div class="card bg-darker border-${insight.type} mb-2">
                                    <div class="card-body py-2">
                                        <div class="d-flex align-items-start">
                                            <i class="fas fa-${this.getInsightIcon(insight.type)} me-2 mt-1 text-${insight.type}"></i>
                                            <div class="flex-grow-1">
                                                <strong class="d-block text-${insight.type}">${insight.title}</strong>
                                                <small class="text-muted">${insight.message}</small>
                                                ${insight.recommendation ? `
                                                    <div class="mt-1">
                                                        <small><strong>Recommendation:</strong> ${insight.recommendation}</small>
                                                    </div>
                                                ` : ''}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- Quick Charts Preview -->
            ${results.chart_data && Object.keys(results.chart_data).length > 0 ? `
                <div class="charts-preview mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="text-info mb-0">
                            <i class="fas fa-chart-bar me-1"></i> Data Visualizations
                        </h6>
                        <button class="btn btn-sm btn-outline-primary view-all-charts" 
                                data-results='${JSON.stringify(results)}'>
                            <i class="fas fa-expand me-1"></i> View All
                        </button>
                    </div>
                    <div class="row g-2" id="previewCharts">
                        <!-- Charts will be rendered here -->
                    </div>
                </div>
            ` : ''}

            <!-- Actions -->
            <div class="response-actions mt-3 pt-2 border-top border-secondary">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-success export-results" 
                            data-results='${JSON.stringify(results.table_data)}'>
                        <i class="fas fa-file-csv me-1"></i> Export CSV
                    </button>
                    <button class="btn btn-outline-info view-details" 
                            data-results='${JSON.stringify(results)}'>
                        <i class="fas fa-search me-1"></i> Detailed View
                    </button>
                    <button class="btn btn-outline-warning refine-search" 
                            data-question="${this.escapeHtml(question)}">
                        <i class="fas fa-edit me-1"></i> Refine Search
                    </button>
                </div>
            </div>
        `;
    }

    initializePreviewCharts(chartData, container) {
        if (!chartData || Object.keys(chartData).length === 0) return;

        const previewContainer = container.querySelector('#previewCharts');
        if (!previewContainer) return;

        // Show first chart as preview
        const firstChartType = Object.keys(chartData)[0];
        const chartId = `preview-${firstChartType}-${Date.now()}`;
        
        previewContainer.innerHTML = `
            <div class="col-12">
                <div class="card bg-darker border-0">
                    <div class="card-body p-2">
                        <h6 class="card-title text-center mb-2">${this.formatChartTitle(firstChartType)}</h6>
                        <div class="chart-container-sm">
                            <canvas id="${chartId}"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.renderSingleChart(firstChartType, chartData[firstChartType], chartId);
    }

    displayQueryResults(data) {
        // Destroy existing charts before rendering new ones
        this.destroyAllCharts();
        
        this.currentResults = data;
        const resultsSection = document.getElementById('resultsSection');
        
        if (!resultsSection) return;

        resultsSection.innerHTML = this.createResultsHTML(data);
        this.showExportButton();

        // Initialize charts after a short delay to ensure DOM is ready
        setTimeout(() => {
            this.initializeMainCharts(data.results.chart_data, resultsSection);
        }, 100);
    }

    createResultsHTML(data) {
        const { results } = data;
        
        return `
            <div class="results-container mt-4">
                <!-- Charts Section -->
                ${results.chart_data && Object.keys(results.chart_data).length > 0 ? `
                    <div class="card bg-darker border-0 shadow mb-4">
                        <div class="card-header bg-gradient-dark border-0">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-0">
                                        <i class="fas fa-chart-bar text-primary me-2"></i>
                                        Interactive Visualizations
                                    </h6>
                                    <small class="text-muted">${Object.keys(results.chart_data).length} charts generated</small>
                                </div>
                                <button class="btn btn-sm btn-outline-success export-all-charts">
                                    <i class="fas fa-download me-1"></i> Export All
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="charts-grid row g-4" id="mainChartsGrid">
                                ${Object.keys(results.chart_data).map((chartType, index) => `
                                    <div class="col-lg-6">
                                        <div class="chart-wrapper card bg-darker border-0 h-100" data-chart-type="${chartType}">
                                            <div class="card-header bg-dark border-0">
                                                <div class="d-flex justify-content-between align-items-center">
                                                    <h6 class="mb-0 text-capitalize">${this.formatChartTitle(chartType)}</h6>
                                                    <div class="chart-controls">
                                                        <button class="btn btn-sm btn-outline-secondary chart-export" data-chart-id="main-${chartType}-${index}">
                                                            <i class="fas fa-download"></i>
                                                        </button>
                                                        <button class="btn btn-sm btn-outline-secondary chart-fullscreen" data-chart-id="main-${chartType}-${index}">
                                                            <i class="fas fa-expand"></i>
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="card-body">
                                                <div class="chart-container">
                                                    <canvas id="main-${chartType}-${index}"></canvas>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                ` : ''}

                <!-- Events Table -->
                <div class="card bg-darker border-0 shadow">
                    <div class="card-header bg-gradient-dark border-0">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-0">
                                    <i class="fas fa-table text-success me-2"></i>
                                    Event Details
                                </h6>
                                <small class="text-muted">Showing ${results.sampled_events} of ${results.total_events} total events</small>
                            </div>
                            <button class="btn btn-sm btn-outline-primary" id="viewAllEvents">
                                <i class="fas fa-list me-1"></i> View All
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        ${this.createDetailedEventsTable(results.table_data)}
                    </div>
                </div>
            </div>
        `;
    }

    createDetailedEventsTable(events) {
        if (!events || events.length === 0) {
            return '<p class="text-muted text-center py-4">No events found.</p>';
        }

        return `
            <div class="table-responsive">
                <table class="table table-dark table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Event Type</th>
                            <th>Source IP</th>
                            <th>User</th>
                            <th>Severity</th>
                            <th>Country</th>
                            <th>Risk Score</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${events.map(event => `
                            <tr>
                                <td>${this.formatDate(event.timestamp)}</td>
                                <td>
                                    <span class="badge bg-secondary text-capitalize">
                                        ${event.event_type.replace('_', ' ')}
                                    </span>
                                </td>
                                <td><code class="text-info">${event.source_ip}</code></td>
                                <td>${event.user}</td>
                                <td>
                                    <span class="badge ${this.getSeverityBadgeClass(event.severity)}">
                                        ${event.severity}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge bg-dark">
                                        <i class="fas fa-globe me-1"></i>${event.country}
                                    </span>
                                </td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="progress flex-grow-1 me-2" style="height: 6px;">
                                            <div class="progress-bar ${this.getRiskScoreClass(event.risk_score)}" 
                                                 style="width: ${event.risk_score}%"></div>
                                        </div>
                                        <small>${event.risk_score}</small>
                                    </div>
                                </td>
                                <td><small class="text-muted">${this.escapeHtml(event.message)}</small></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    initializeMainCharts(chartData, container) {
        if (!chartData) return;

        Object.keys(chartData).forEach((chartType, index) => {
            const chartId = `main-${chartType}-${index}`;
            this.renderSingleChart(chartType, chartData[chartType], chartId);
        });
    }

    renderSingleChart(chartType, chartData, chartId) {
        // Destroy existing chart if it exists
        const existingChart = this.currentCharts.find(chart => chart.canvas.id === chartId);
        if (existingChart) {
            existingChart.destroy();
            this.currentCharts = this.currentCharts.filter(chart => chart !== existingChart);
        }

        const canvas = document.getElementById(chartId);
        if (!canvas) {
            console.warn(`Canvas element with id ${chartId} not found`);
            return;
        }

        const ctx = canvas.getContext('2d');
        let chart;

        try {
            switch (chartType) {
                case 'timeline':
                    chart = this.createTimelineChart(ctx, chartData);
                    break;
                case 'event_types':
                    chart = this.createDoughnutChart(ctx, chartData, 'Event Types Distribution');
                    break;
                case 'severity_distribution':
                    chart = this.createDoughnutChart(ctx, chartData, 'Severity Distribution');
                    break;
                case 'top_users':
                    chart = this.createBarChart(ctx, chartData, 'Top Users by Activity');
                    break;
                case 'geo_distribution':
                    chart = this.createBarChart(ctx, chartData, 'Geographic Distribution');
                    break;
                default:
                    console.warn(`Unknown chart type: ${chartType}`);
                    return;
            }

            if (chart) {
                this.currentCharts.push(chart);
            }
        } catch (error) {
            console.error(`Error rendering chart ${chartType}:`, error);
        }
    }

    createTimelineChart(ctx, data) {
        const labels = data.labels.map(label => {
            const date = new Date(label);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        });

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Events',
                    data: data.values,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            maxTicksLimit: 8
                        }
                    }
                }
            }
        });
    }

    createDoughnutChart(ctx, data, title) {
        const colors = ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c'];
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: colors,
                    borderColor: colors.map(color => color.replace('0.2', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            padding: 15
                        }
                    },
                    title: {
                        display: false,
                        text: title
                    }
                }
            }
        });
    }

    createBarChart(ctx, data, title) {
        const colors = data.labels.map((_, i) => {
            const hue = (i * 137.5) % 360;
            return `hsl(${hue}, 70%, 50%)`;
        });

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Count',
                    data: data.values,
                    backgroundColor: colors,
                    borderColor: colors.map(color => color.replace('0.8', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: false,
                        text: title
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    }

    destroyAllCharts() {
        this.currentCharts.forEach(chart => {
            try {
                chart.destroy();
            } catch (error) {
                console.warn('Error destroying chart:', error);
            }
        });
        this.currentCharts = [];
    }

    showFullResults(results) {
        const modalBody = document.getElementById('modalBody');
        if (!modalBody) return;

        modalBody.innerHTML = this.createFullResultsModal(results);
        
        // Initialize modal charts
        setTimeout(() => {
            this.initializeModalCharts(results.chart_data);
        }, 100);
        
        const modal = new bootstrap.Modal(document.getElementById('resultsModal'));
        modal.show();
    }

    createFullResultsModal(results) {
        return `
            <div class="container-fluid">
                <div class="row">
                    <div class="col-12">
                        <!-- Summary -->
                        <div class="card bg-darker border-0 mb-4">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="fas fa-chart-bar me-2 text-primary"></i>
                                    Comprehensive Analysis
                                </h5>
                                <p class="card-text">${results.summary}</p>
                                <div class="row text-center">
                                    <div class="col">
                                        <h4 class="text-primary">${results.total_events}</h4>
                                        <small class="text-muted">Total Events</small>
                                    </div>
                                    <div class="col">
                                        <h4 class="text-warning">${Object.keys(results.analysis?.event_types || {}).length}</h4>
                                        <small class="text-muted">Event Types</small>
                                    </div>
                                    <div class="col">
                                        <h4 class="text-info">${Object.keys(results.analysis?.top_source_ips || {}).length}</h4>
                                        <small class="text-muted">Source IPs</small>
                                    </div>
                                    <div class="col">
                                        <h4 class="text-success">${Object.keys(results.analysis?.top_users || {}).length}</h4>
                                        <small class="text-muted">Users</small>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Charts Grid -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="mb-3">
                                    <i class="fas fa-chart-line me-2 text-info"></i>
                                    Data Visualizations
                                </h5>
                                <div class="row g-4" id="modalChartsGrid">
                                    <!-- Charts will be rendered here -->
                                </div>
                            </div>
                        </div>

                        <!-- Data Table -->
                        <div class="row">
                            <div class="col-12">
                                <h5 class="mb-3">
                                    <i class="fas fa-table me-2 text-success"></i>
                                    Event Details (${results.sampled_events} sampled)
                                </h5>
                                <div class="table-responsive">
                                    <table class="table table-dark table-striped table-hover">
                                        <thead>
                                            <tr>
                                                <th>Timestamp</th>
                                                <th>Source IP</th>
                                                <th>Destination IP</th>
                                                <th>Event Type</th>
                                                <th>Severity</th>
                                                <th>User</th>
                                                <th>Message</th>
                                                <th>Risk Score</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${results.table_data.slice(0, 50).map(event => `
                                                <tr>
                                                    <td>${this.formatDate(event.timestamp)}</td>
                                                    <td><code class="text-info">${event.source_ip}</code></td>
                                                    <td><code class="text-warning">${event.destination_ip}</code></td>
                                                    <td><span class="badge bg-secondary">${event.event_type}</span></td>
                                                    <td><span class="badge ${this.getSeverityBadgeClass(event.severity)}">${event.severity}</span></td>
                                                    <td>${event.user}</td>
                                                    <td><small>${this.escapeHtml(event.message)}</small></td>
                                                    <td>
                                                        <div class="progress" style="height: 6px;">
                                                            <div class="progress-bar ${this.getRiskScoreClass(event.risk_score)}" 
                                                                 style="width: ${event.risk_score}%"></div>
                                                        </div>
                                                        <small>${event.risk_score}</small>
                                                    </td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    initializeModalCharts(chartData) {
        const container = document.getElementById('modalChartsGrid');
        if (!container || !chartData) return;

        Object.keys(chartData).forEach((chartType, index) => {
            const chartId = `modal-chart-${chartType}-${index}`;
            const colSize = Object.keys(chartData).length <= 2 ? 'col-md-6' : 'col-md-6 col-lg-4';
            
            container.innerHTML += `
                <div class="${colSize}">
                    <div class="card bg-darker border-0 h-100">
                        <div class="card-body">
                            <h6 class="card-title text-capitalize text-center">${this.formatChartTitle(chartType)}</h6>
                            <div class="chart-container-modal">
                                <canvas id="${chartId}"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            setTimeout(() => {
                this.renderSingleChart(chartType, chartData[chartType], chartId);
            }, 100);
        });
    }

    // Utility methods
    addMessage(text, type, isError = false) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message ${isError ? 'error-message' : ''}`;
        
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="flex-grow-1">
                    <strong>${type === 'user' ? 'You' : 'SIEM Assistant'}:</strong>
                    <span>${this.escapeHtml(text)}</span>
                </div>
                <small class="text-muted ms-2">${new Date().toLocaleTimeString()}</small>
            </div>
        `;

        // Remove welcome message if it exists
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const sendButton = document.getElementById('sendButton');
        const questionInput = document.getElementById('questionInput');

        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (sendButton) {
            sendButton.disabled = true;
            sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
        if (questionInput) questionInput.disabled = true;
    }

    hideLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const sendButton = document.getElementById('sendButton');
        const questionInput = document.getElementById('questionInput');

        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.innerHTML = '<i class="fas fa-paper-plane"></i> Ask';
        }
        if (questionInput) {
            questionInput.disabled = false;
            questionInput.focus();
        }
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    showError(message) {
        this.addMessage(message, 'bot', true);
    }

    showExportButton() {
        const exportBtn = document.getElementById('exportResults');
        if (exportBtn) {
            exportBtn.style.display = 'inline-block';
        }
    }

    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="welcome-message text-center text-muted py-5">
                    <i class="fas fa-robot fa-3x mb-3 opacity-50"></i>
                    <h5>Welcome to SIEM Assistant</h5>
                    <p class="mb-3">Ask me questions about your security data or use the filters above to explore</p>
                    <div class="row g-2 justify-content-center">
                        <div class="col-auto">
                            <small class="badge bg-primary">Try: "Show failed logins from yesterday"</small>
                        </div>
                        <div class="col-auto">
                            <small class="badge bg-success">Try: "Display top threat sources"</small>
                        </div>
                        <div class="col-auto">
                            <small class="badge bg-warning">Try: "Malware events this week"</small>
                        </div>
                    </div>
                </div>
            `;
        }
        
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.innerHTML = '';
        }
        
        this.destroyAllCharts();
        this.conversationHistory = [];
        
        const exportBtn = document.getElementById('exportResults');
        if (exportBtn) {
            exportBtn.style.display = 'none';
        }
    }

    getInsightIcon(type) {
        const icons = {
            'warning': 'exclamation-triangle',
            'danger': 'skull-crossbones',
            'info': 'info-circle',
            'success': 'check-circle'
        };
        return icons[type] || 'info-circle';
    }

    getSeverityBadgeClass(severity) {
        const classMap = {
            'critical': 'bg-danger',
            'high': 'bg-warning',
            'medium': 'bg-info',
            'low': 'bg-success'
        };
        return classMap[severity] || 'bg-secondary';
    }

    getRiskScoreClass(score) {
        if (score >= 80) return 'bg-danger';
        if (score >= 60) return 'bg-warning';
        if (score >= 40) return 'bg-info';
        return 'bg-success';
    }

    formatChartTitle(chartType) {
        const titleMap = {
            'timeline': 'Events Timeline',
            'event_types': 'Event Type Distribution',
            'severity_distribution': 'Severity Levels',
            'top_source_ips': 'Top Source IPs',
            'threat_indicators': 'Threat Indicators',
            'geo_distribution': 'Geographic Distribution',
            'top_users': 'Top Users by Activity',
            'protocol_distribution': 'Protocol Distribution'
        };
        return titleMap[chartType] || chartType.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    exportResultsAsCSV(results) {
        if (!results || results.length === 0) {
            alert('No data to export');
            return;
        }

        const headers = Object.keys(results[0]);
        const csvContent = [
            headers.join(','),
            ...results.map(row => headers.map(header => {
                const value = row[header];
                return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
            }).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `siemspeak-export-${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    }

    exportCurrentResults() {
        if (this.currentResults && this.currentResults.results.table_data) {
            this.exportResultsAsCSV(this.currentResults.results.table_data);
        } else {
            alert('No results available to export');
        }
    }

    exportChart(chartId) {
        const chart = this.currentCharts.find(c => c.canvas.id === chartId);
        if (chart) {
            const link = document.createElement('a');
            link.download = `chart-${chartId}-${new Date().toISOString().split('T')[0]}.png`;
            link.href = chart.toBase64Image();
            link.click();
        }
    }

    toggleFullscreenChart(chartId) {
        const chartWrapper = document.querySelector(`[data-chart-id="${chartId}"]`)?.closest('.chart-wrapper');
        if (chartWrapper) {
            chartWrapper.classList.toggle('fullscreen');
            
            if (chartWrapper.classList.contains('fullscreen')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }

            // Update chart size
            const chart = this.currentCharts.find(c => c.canvas.id === chartId);
            if (chart) {
                setTimeout(() => {
                    chart.resize();
                }, 100);
            }
        }
    }

    updateOverviewCards() {
        // Mock data for overview cards
        const mockData = {
            totalEvents: 10247,
            threatsBlocked: 347,
            highSeverity: 89,
            activeUsers: 142,
            malwareEvents: 23,
            countriesCount: 14
        };

        Object.keys(mockData).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.textContent = this.formatNumber(mockData[key]);
            }
        });
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    showDetailedAnalysis(results) {
        this.showFullResults(results);
    }

    handleAutocomplete(query) {
        // Basic autocomplete implementation
        if (query.length < 2) return;
        
        // You can implement more sophisticated autocomplete here
        console.log('Autocomplete query:', query);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.siemSpeakDashboard = new SIEMSpeakDashboard();
    window.siemSpeakDashboard.init();
    
    // Check for URL parameters (for example queries from homepage)
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query');
    if (query) {
        document.getElementById('questionInput').value = query;
        window.siemSpeakDashboard.sendQuestion(query);
    }
});