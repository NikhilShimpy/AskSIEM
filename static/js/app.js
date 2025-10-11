// Main application JavaScript for SIEMSpeak

class SIEMSpeakApp {
    constructor() {
        this.currentCharts = [];
        this.conversationHistory = [];
        this.isDarkTheme = true;
        this.currentFilters = {};
    }

    init() {
        this.bindEvents();
        this.setupTheme();
        this.loadConversationHistory();
        this.setupAutoComplete();
    }

    bindEvents() {
        // Theme toggle
        document.getElementById('themeToggle')?.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Example queries
        document.querySelectorAll('.example-query').forEach(button => {
            button.addEventListener('click', (e) => {
                const query = e.currentTarget.getAttribute('data-query');
                this.fillQueryInput(query);
            });
        });

        // Example buttons on homepage
        document.querySelectorAll('.example-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const query = e.currentTarget.getAttribute('data-query');
                this.fillQueryInput(query);
            });
        });

        // Clear chat
        document.getElementById('clearChat')?.addEventListener('click', () => {
            this.clearConversation();
        });

        // Export results
        document.getElementById('exportResults')?.addEventListener('click', () => {
            this.exportResults();
        });
    }

    setupTheme() {
        // Check for saved theme preference or respect OS preference
        const savedTheme = localStorage.getItem('theme') || 
                          (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        this.isDarkTheme = theme === 'dark';
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);

        // Update theme toggle button
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.innerHTML = this.isDarkTheme ? 
                '<i class="fas fa-sun"></i>' : 
                '<i class="fas fa-moon"></i>';
        }

        // Re-render charts with new theme
        this.refreshCharts();
    }

    toggleTheme() {
        const newTheme = this.isDarkTheme ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    fillQueryInput(query) {
        const input = document.getElementById('questionInput');
        if (input) {
            input.value = query;
            input.focus();
            
            // If we're on the dashboard, trigger the query
            if (window.SIEMSpeakDashboard) {
                window.SIEMSpeakDashboard.sendQuestion(query);
            }
        }
    }

    setupAutoComplete() {
        const input = document.getElementById('questionInput');
        if (!input) return;

        let timeoutId;

        input.addEventListener('input', (e) => {
            clearTimeout(timeoutId);
            const query = e.target.value.trim();
            
            if (query.length > 2) {
                timeoutId = setTimeout(() => {
                    this.fetchAutoCompleteSuggestions(query);
                }, 300);
            }
        });

        // Handle arrow key navigation for autocomplete
        input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateAutocomplete(e.key);
            } else if (e.key === 'Enter' && this.isAutocompleteActive()) {
                e.preventDefault();
                this.selectAutocompleteSuggestion();
            } else if (e.key === 'Escape') {
                this.hideAutocomplete();
            }
        });

        // Hide autocomplete when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.autocomplete-container') && !e.target.closest('#questionInput')) {
                this.hideAutocomplete();
            }
        });
    }

    async fetchAutoCompleteSuggestions(query) {
        try {
            const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                this.showAutocompleteSuggestions(data.suggestions);
            } else {
                this.hideAutocomplete();
            }
        } catch (error) {
            console.warn('Autocomplete fetch failed:', error);
            this.hideAutocomplete();
        }
    }

    showAutocompleteSuggestions(suggestions) {
        this.hideAutocomplete();

        const input = document.getElementById('questionInput');
        const container = document.createElement('div');
        container.className = 'autocomplete-container position-absolute bg-dark border border-secondary rounded mt-1 z-3';
        container.style.width = input.offsetWidth + 'px';
        container.style.top = (input.offsetTop + input.offsetHeight) + 'px';
        container.style.left = input.offsetLeft + 'px';

        suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = `autocomplete-item px-3 py-2 border-bottom border-secondary cursor-pointer ${index === 0 ? 'active' : ''}`;
            item.textContent = suggestion;
            item.setAttribute('data-index', index);
            
            item.addEventListener('click', () => {
                input.value = suggestion;
                this.hideAutocomplete();
                input.focus();
            });

            item.addEventListener('mouseenter', () => {
                this.setActiveAutocompleteItem(index);
            });

            container.appendChild(item);
        });

        // Remove last border
        container.lastChild.classList.remove('border-bottom');

        document.body.appendChild(container);
        this.autocompleteContainer = container;
        this.autocompleteItems = container.querySelectorAll('.autocomplete-item');
        this.activeAutocompleteIndex = 0;
    }

    hideAutocomplete() {
        if (this.autocompleteContainer) {
            this.autocompleteContainer.remove();
            this.autocompleteContainer = null;
            this.autocompleteItems = null;
            this.activeAutocompleteIndex = 0;
        }
    }

    isAutocompleteActive() {
        return this.autocompleteContainer && this.autocompleteItems.length > 0;
    }

    navigateAutocomplete(direction) {
        if (!this.isAutocompleteActive()) return;

        const items = this.autocompleteItems;
        items[this.activeAutocompleteIndex].classList.remove('active');

        if (direction === 'ArrowDown') {
            this.activeAutocompleteIndex = (this.activeAutocompleteIndex + 1) % items.length;
        } else {
            this.activeAutocompleteIndex = (this.activeAutocompleteIndex - 1 + items.length) % items.length;
        }

        items[this.activeAutocompleteIndex].classList.add('active');
    }

    selectAutocompleteSuggestion() {
        if (!this.isAutocompleteActive()) return;

        const activeItem = this.autocompleteItems[this.activeAutocompleteIndex];
        const input = document.getElementById('questionInput');
        input.value = activeItem.textContent;
        this.hideAutocomplete();
        input.focus();
    }

    setActiveAutocompleteItem(index) {
        if (!this.isAutocompleteActive()) return;

        this.autocompleteItems[this.activeAutocompleteIndex].classList.remove('active');
        this.activeAutocompleteIndex = index;
        this.autocompleteItems[this.activeAutocompleteIndex].classList.add('active');
    }

    refreshCharts() {
        // Destroy all current charts
        this.currentCharts.forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.currentCharts = [];

        // Re-render charts if we have chart data
        if (this.lastChartData) {
            setTimeout(() => {
                this.renderCharts(this.lastChartData);
            }, 100);
        }
    }

    renderCharts(chartData, container = document.body) {
        this.lastChartData = chartData;
        
        if (!chartData || Object.keys(chartData).length === 0) {
            return;
        }

        // Find all chart containers in the specified container
        const chartContainers = container.querySelectorAll('[data-chart-type]');
        
        chartContainers.forEach((chartContainer, index) => {
            const chartType = chartContainer.getAttribute('data-chart-type');
            const chartId = chartContainer.getAttribute('data-chart-id') || `chart-${Date.now()}-${index}`;
            
            if (chartData[chartType]) {
                this.renderSingleChart(chartType, chartData[chartType], chartId, chartContainer);
            }
        });
    }

    renderSingleChart(chartType, data, chartId, container) {
        const canvas = container.querySelector('canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const theme = this.isDarkTheme ? this.darkTheme : this.lightTheme;

        let chartConfig;

        switch (chartType) {
            case 'timeline':
                chartConfig = this.createTimelineChart(data, theme);
                break;
            case 'event_types':
                chartConfig = this.createEventTypesChart(data, theme);
                break;
            case 'severity_distribution':
                chartConfig = this.createSeverityChart(data, theme);
                break;
            case 'top_users':
                chartConfig = this.createTopUsersChart(data, theme);
                break;
            case 'geo_distribution':
                chartConfig = this.createGeoChart(data, theme);
                break;
            default:
                chartConfig = this.createDefaultChart(data, theme, chartType);
        }

        if (chartConfig) {
            try {
                const chart = new Chart(ctx, chartConfig);
                this.currentCharts.push(chart);
            } catch (error) {
                console.error('Error rendering chart:', error);
                this.showChartError(container, error.message);
            }
        }
    }

    createTimelineChart(data, theme) {
        const labels = data.labels.map(label => {
            const date = new Date(label);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        });

        return {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Events',
                    data: data.values,
                    borderColor: theme.colors[0],
                    backgroundColor: this.hexToRgba(theme.colors[0], 0.1),
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: theme.colors[0],
                    pointBorderColor: theme.background,
                    pointBorderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: theme.tooltipBg,
                        titleColor: theme.tooltipText,
                        bodyColor: theme.tooltipText,
                        borderColor: theme.border,
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: theme.grid
                        },
                        ticks: {
                            color: theme.text,
                            maxRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: theme.grid
                        },
                        ticks: {
                            color: theme.text,
                            precision: 0
                        }
                    }
                }
            }
        };
    }

    createEventTypesChart(data, theme) {
        return {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: data.labels.map((_, index) => 
                        this.getColorByIndex(index, theme.colors)
                    ),
                    borderColor: theme.background,
                    borderWidth: 2,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: theme.text,
                            usePointStyle: true,
                            padding: 15
                        }
                    }
                }
            }
        };
    }

    createSeverityChart(data, theme) {
        const severityColors = {
            'critical': theme.danger,
            'high': theme.warning,
            'medium': theme.info,
            'low': theme.success
        };

        return {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Events',
                    data: data.values,
                    backgroundColor: data.labels.map(label => 
                        severityColors[label] || theme.colors[0]
                    ),
                    borderColor: data.labels.map(label => 
                        severityColors[label] || theme.colors[0]
                    ),
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: theme.grid
                        },
                        ticks: {
                            color: theme.text
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: theme.grid
                        },
                        ticks: {
                            color: theme.text,
                            precision: 0
                        }
                    }
                }
            }
        };
    }

    createTopUsersChart(data, theme) {
        return {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Activity Count',
                    data: data.values,
                    backgroundColor: theme.colors[0],
                    borderColor: theme.colors[0],
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: theme.grid
                        },
                        ticks: {
                            color: theme.text,
                            precision: 0
                        }
                    },
                    y: {
                        grid: {
                            color: theme.grid
                        },
                        ticks: {
                            color: theme.text
                        }
                    }
                }
            }
        };
    }

    createGeoChart(data, theme) {
        return {
            type: 'polarArea',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: data.labels.map((_, index) => 
                        this.hexToRgba(this.getColorByIndex(index, theme.colors), 0.7)
                    ),
                    borderColor: data.labels.map((_, index) => 
                        this.getColorByIndex(index, theme.colors)
                    ),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: theme.text
                        }
                    }
                }
            }
        };
    }

    createDefaultChart(data, theme, chartType) {
        return {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: chartType.split('_').map(word => 
                        word.charAt(0).toUpperCase() + word.slice(1)
                    ).join(' '),
                    data: data.values,
                    backgroundColor: theme.colors[0],
                    borderColor: theme.colors[0],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: theme.text
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: theme.grid
                        },
                        ticks: {
                            color: theme.text
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: theme.grid
                        },
                        ticks: {
                            color: theme.text
                        }
                    }
                }
            }
        };
    }

    showChartError(container, message) {
        container.innerHTML = `
            <div class="chart-error text-center p-4">
                <i class="fas fa-exclamation-triangle text-warning fa-2x mb-3"></i>
                <p class="text-muted">Failed to render chart: ${message}</p>
            </div>
        `;
    }

    // Utility methods
    getColorByIndex(index, colors) {
        return colors[index % colors.length];
    }

    hexToRgba(hex, alpha = 1) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    async loadConversationHistory() {
        try {
            const response = await fetch('/conversation');
            const data = await response.json();
            
            if (data.conversation && data.conversation.length > 0) {
                this.conversationHistory = data.conversation;
                this.displayConversationHistory();
            }
        } catch (error) {
            console.warn('Failed to load conversation history:', error);
        }
    }

    displayConversationHistory() {
        // This would be implemented in the dashboard-specific code
        console.log('Conversation history loaded:', this.conversationHistory);
    }

    async clearConversation() {
        if (!confirm('Are you sure you want to clear the conversation history?')) {
            return;
        }

        try {
            await fetch('/clear', { method: 'POST' });
            this.conversationHistory = [];
            
            // Clear UI
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.innerHTML = `
                    <div class="welcome-message text-center text-muted py-5">
                        <i class="fas fa-robot fa-3x mb-3 opacity-50"></i>
                        <h5>Welcome to SIEM Assistant</h5>
                        <p class="mb-3">Ask me questions about your security data</p>
                    </div>
                `;
            }

            // Clear results section
            const resultsSection = document.getElementById('resultsSection');
            if (resultsSection) {
                resultsSection.innerHTML = '';
            }

            // Hide export button
            const exportBtn = document.getElementById('exportResults');
            if (exportBtn) {
                exportBtn.style.display = 'none';
            }

            // Clear charts
            this.currentCharts.forEach(chart => chart.destroy());
            this.currentCharts = [];

        } catch (error) {
            console.error('Failed to clear conversation:', error);
            alert('Failed to clear conversation history');
        }
    }

    exportResults() {
        // This would export the current results as CSV or PDF
        console.log('Exporting results...');
        // Implementation would depend on specific requirements
    }

    // Theme configurations
    darkTheme = {
        background: '#1a1a1a',
        text: '#ffffff',
        grid: '#333333',
        border: '#444444',
        tooltipBg: '#2d2d2d',
        tooltipText: '#ffffff',
        colors: ['#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236'],
        success: '#28a745',
        warning: '#ffc107',
        danger: '#dc3545',
        info: '#17a2b8'
    };

    lightTheme = {
        background: '#ffffff',
        text: '#333333',
        grid: '#e0e0e0',
        border: '#dee2e6',
        tooltipBg: '#f8f9fa',
        tooltipText: '#333333',
        colors: ['#3366cc', '#dc3912', '#ff9900', '#109618', '#990099'],
        success: '#28a745',
        warning: '#ffc107',
        danger: '#dc3545',
        info: '#17a2b8'
    };
}

// Initialize the main application
document.addEventListener('DOMContentLoaded', function() {
    window.SIEMSpeakApp = new SIEMSpeakApp();
    window.SIEMSpeakApp.init();
});

// Utility functions for the whole application
window.SIEMSpeakUtils = {
    formatNumber: (num) => {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },

    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    formatDuration: (seconds) => {
        if (seconds < 60) {
            return seconds + 's';
        } else if (seconds < 3600) {
            return Math.floor(seconds / 60) + 'm';
        } else {
            return Math.floor(seconds / 3600) + 'h';
        }
    },

    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    throttle: (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};