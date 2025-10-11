// Charts configuration and utilities for SIEMSpeak

class SIEMSpeakCharts {
    constructor() {
        this.chartInstances = new Map();
        this.defaultConfig = this.getDefaultConfig();
    }

    getDefaultConfig() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#444444',
                    borderWidth: 1,
                    cornerRadius: 6,
                    displayColors: true
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            },
            elements: {
                line: {
                    tension: 0.4
                },
                point: {
                    hoverRadius: 6,
                    radius: 3
                }
            }
        };
    }

    createChart(canvasId, type, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element with id '${canvasId}' not found`);
            return null;
        }

        // Destroy existing chart if it exists
        if (this.chartInstances.has(canvasId)) {
            this.chartInstances.get(canvasId).destroy();
        }

        const ctx = canvas.getContext('2d');
        const mergedOptions = this.mergeOptions(type, options);

        try {
            const chart = new Chart(ctx, {
                type: type,
                data: data,
                options: mergedOptions
            });

            this.chartInstances.set(canvasId, chart);
            return chart;
        } catch (error) {
            console.error(`Error creating chart '${canvasId}':`, error);
            return null;
        }
    }

    mergeOptions(chartType, customOptions) {
        const baseOptions = JSON.parse(JSON.stringify(this.defaultConfig));
        
        // Type-specific options
        const typeSpecificOptions = this.getTypeSpecificOptions(chartType);
        
        // Merge all options
        return this.deepMerge(baseOptions, typeSpecificOptions, customOptions);
    }

    getTypeSpecificOptions(chartType) {
        const commonScales = {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.7)'
                }
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.7)'
                },
                beginAtZero: true
            }
        };

        switch (chartType) {
            case 'line':
                return {
                    scales: commonScales,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                };

            case 'bar':
                return {
                    scales: commonScales,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                };

            case 'horizontalBar':
                return {
                    indexAxis: 'y',
                    scales: {
                        x: commonScales.x,
                        y: commonScales.y
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                };

            case 'doughnut':
            case 'pie':
                return {
                    cutout: chartType === 'doughnut' ? '60%' : 0,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                };

            case 'polarArea':
                return {
                    scales: {
                        r: {
                            ticks: {
                                display: false
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    }
                };

            case 'radar':
                return {
                    scales: {
                        r: {
                            angleLines: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            pointLabels: {
                                color: 'rgba(255, 255, 255, 0.7)'
                            },
                            ticks: {
                                display: false
                            }
                        }
                    }
                };

            default:
                return {
                    scales: commonScales
                };
        }
    }

    deepMerge(target, ...sources) {
        if (!sources.length) return target;
        const source = sources.shift();

        if (this.isObject(target) && this.isObject(source)) {
            for (const key in source) {
                if (this.isObject(source[key])) {
                    if (!target[key]) Object.assign(target, { [key]: {} });
                    this.deepMerge(target[key], source[key]);
                } else {
                    Object.assign(target, { [key]: source[key] });
                }
            }
        }

        return this.deepMerge(target, ...sources);
    }

    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }

    // Color schemes
    getColorScheme(schemeName = 'primary', theme = 'dark') {
        const schemes = {
            primary: {
                dark: ['#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236'],
                light: ['#3366cc', '#dc3912', '#ff9900', '#109618', '#990099']
            },
            warm: {
                dark: ['#ff6b6b', '#ffa726', '#ffca28', '#66bb6a', '#42a5f5'],
                light: ['#ef5350', '#ffa726', '#ffca28', '#66bb6a', '#42a5f5']
            },
            cool: {
                dark: ['#5c6bc0', '#26c6da', '#26a69a', '#9ccc65', '#d4e157'],
                light: ['#5c6bc0', '#26c6da', '#26a69a', '#9ccc65', '#d4e157']
            },
            severity: {
                dark: {
                    critical: '#dc3545',
                    high: '#fd7e14',
                    medium: '#ffc107',
                    low: '#28a745'
                },
                light: {
                    critical: '#dc3545',
                    high: '#fd7e14',
                    medium: '#ffc107',
                    low: '#28a745'
                }
            }
        };

        return schemes[schemeName]?.[theme] || schemes.primary[theme];
    }

    // Data transformation utilities
    transformTimelineData(rawData, interval = 'hour') {
        if (!rawData || !rawData.labels || !rawData.values) {
            return null;
        }

        return {
            labels: rawData.labels.map(label => {
                const date = new Date(label);
                switch (interval) {
                    case 'minute':
                        return date.toLocaleTimeString([], { minute: '2-digit', second: '2-digit' });
                    case 'hour':
                        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    case 'day':
                        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
                    default:
                        return date.toLocaleTimeString();
                }
            }),
            datasets: [{
                label: 'Events',
                data: rawData.values,
                borderColor: this.getColorScheme('primary', 'dark')[0],
                backgroundColor: this.hexToRgba(this.getColorScheme('primary', 'dark')[0], 0.1),
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        };
    }

    transformDistributionData(rawData, scheme = 'primary') {
        if (!rawData || !rawData.labels || !rawData.values) {
            return null;
        }

        const colors = this.getColorScheme(scheme, 'dark');
        
        return {
            labels: rawData.labels,
            datasets: [{
                data: rawData.values,
                backgroundColor: rawData.labels.map((_, index) => 
                    this.hexToRgba(colors[index % colors.length], 0.8)
                ),
                borderColor: rawData.labels.map((_, index) => colors[index % colors.length]),
                borderWidth: 2
            }]
        };
    }

    transformBarData(rawData, horizontal = false, scheme = 'primary') {
        if (!rawData || !rawData.labels || !rawData.values) {
            return null;
        }

        const colors = this.getColorScheme(scheme, 'dark');
        
        return {
            labels: rawData.labels,
            datasets: [{
                label: 'Count',
                data: rawData.values,
                backgroundColor: rawData.values.map((_, index) => 
                    this.hexToRgba(colors[index % colors.length], 0.8)
                ),
                borderColor: rawData.values.map((_, index) => colors[index % colors.length]),
                borderWidth: 1,
                borderRadius: 4
            }]
        };
    }

    // Utility methods
    hexToRgba(hex, alpha = 1) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    downloadChart(chartId, filename = null) {
        const chart = this.chartInstances.get(chartId);
        if (!chart) {
            console.error(`Chart with id '${chartId}' not found`);
            return;
        }

        const link = document.createElement('a');
        link.download = filename || `chart-${chartId}-${new Date().toISOString().split('T')[0]}.png`;
        link.href = chart.toBase64Image();
        link.click();
    }

    exportChartData(chartId) {
        const chart = this.chartInstances.get(chartId);
        if (!chart) {
            console.error(`Chart with id '${chartId}' not found`);
            return;
        }

        const data = chart.data;
        const csvContent = this.chartDataToCSV(data);
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `chart-data-${chartId}-${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    }

    chartDataToCSV(chartData) {
        if (chartData.datasets.length === 0) return '';

        const headers = ['Label'].concat(chartData.datasets.map(ds => ds.label || 'Dataset'));
        const rows = [headers.join(',')];

        chartData.labels.forEach((label, index) => {
            const row = [label].concat(chartData.datasets.map(ds => ds.data[index] || ''));
            rows.push(row.join(','));
        });

        return rows.join('\n');
    }

    // Chart performance optimization
    debouncedResize(chartId, delay = 250) {
        let timeout;
        const chart = this.chartInstances.get(chartId);
        
        if (!chart) return;

        const resizeHandler = () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                chart.resize();
            }, delay);
        };

        window.addEventListener('resize', resizeHandler);
        
        // Return cleanup function
        return () => {
            window.removeEventListener('resize', resizeHandler);
            clearTimeout(timeout);
        };
    }

    // Chart animation control
    animateChart(chartId, animationType = 'progress') {
        const chart = this.chartInstances.get(chartId);
        if (!chart) return;

        // Reset animation
        chart.data.datasets.forEach((dataset, i) => {
            if (dataset._meta) {
                Object.keys(dataset._meta).forEach(key => {
                    dataset._meta[key].$animations = {};
                });
            }
        });

        chart.update('active');
    }

    // Chart data update
    updateChartData(chartId, newData) {
        const chart = this.chartInstances.get(chartId);
        if (!chart) return;

        chart.data = newData;
        chart.update();
    }

    // Chart destruction and cleanup
    destroyChart(chartId) {
        const chart = this.chartInstances.get(chartId);
        if (chart) {
            chart.destroy();
            this.chartInstances.delete(chartId);
        }
    }

    destroyAllCharts() {
        this.chartInstances.forEach((chart, chartId) => {
            chart.destroy();
            this.chartInstances.delete(chartId);
        });
    }

    // Chart theme adaptation
    adaptChartToTheme(chartId, theme) {
        const chart = this.chartInstances.get(chartId);
        if (!chart) return;

        const colors = this.getColorScheme('primary', theme);
        
        // Update chart colors based on theme
        chart.data.datasets.forEach((dataset, index) => {
            if (dataset.backgroundColor && Array.isArray(dataset.backgroundColor)) {
                dataset.backgroundColor = dataset.backgroundColor.map((_, i) => 
                    this.hexToRgba(colors[i % colors.length], 0.8)
                );
            }
            if (dataset.borderColor && Array.isArray(dataset.borderColor)) {
                dataset.borderColor = dataset.borderColor.map((_, i) => 
                    colors[i % colors.length]
                );
            }
        });

        chart.update();
    }
}

// Initialize charts utility
window.SIEMSpeakCharts = new SIEMSpeakCharts();

// Chart.js global configuration
Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.boxPadding = 6;