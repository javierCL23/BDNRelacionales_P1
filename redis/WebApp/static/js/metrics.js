// Sistema de visualización de métricas en tiempo real

class MetricsDashboard {
    constructor() {
        this.updateInterval = 2000; // Actualizar cada 2 segundos
        this.initializeMetrics();
    }

    async fetchMetrics() {
        try {
            const response = await fetch('/api/metrics');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching metrics:', error);
            return null;
        }
    }

    updateDisplay(metrics) {
        if (!metrics) return;

        // Actualizar visitantes activos
        const activeUsersEl = document.getElementById('active-users');
        if (activeUsersEl && metrics.active_users !== undefined) {
            this.animateValue(activeUsersEl, metrics.active_users);
        }

        // Actualizar peticiones por segundo
        const requestsPerSecEl = document.getElementById('requests-per-sec');
        if (requestsPerSecEl && metrics.requests_per_sec !== undefined) {
            this.animateValue(requestsPerSecEl, metrics.requests_per_sec);
        }

        // Actualizar uso de CPU
        const cpuUsageEl = document.getElementById('cpu-usage');
        if (cpuUsageEl && metrics.cpu_usage !== undefined) {
            cpuUsageEl.textContent = metrics.cpu_usage.toFixed(1) + '%';
            this.updateColorByThreshold(cpuUsageEl, metrics.cpu_usage, 70, 90);
        }

        // Actualizar latencia media
        const avgLatencyEl = document.getElementById('avg-latency');
        if (avgLatencyEl && metrics.avg_latency !== undefined) {
            avgLatencyEl.textContent = metrics.avg_latency.toFixed(0) + 'ms';
            this.updateColorByThreshold(avgLatencyEl, metrics.avg_latency, 100, 300);
        }
    }

    animateValue(element, newValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const increment = (newValue - currentValue) / 10;
        let current = currentValue;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= newValue) || (increment < 0 && current <= newValue)) {
                element.textContent = Math.round(newValue);
                clearInterval(timer);
            } else {
                element.textContent = Math.round(current);
            }
        }, 50);
    }

    updateColorByThreshold(element, value, warningThreshold, dangerThreshold) {
        if (value >= dangerThreshold) {
            element.style.color = '#dc3545'; // Rojo
        } else if (value >= warningThreshold) {
            element.style.color = '#ffc107'; // Amarillo
        } else {
            element.style.color = '#667eea'; // Azul (normal)
        }
    }

    async initializeMetrics() {
        // Primera actualización inmediata
        const initialMetrics = await this.fetchMetrics();
        this.updateDisplay(initialMetrics);

        // Actualización periódica
        setInterval(async () => {
            const metrics = await this.fetchMetrics();
            this.updateDisplay(metrics);
        }, this.updateInterval);
    }
}

// Inicializar dashboard cuando la página cargue
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new MetricsDashboard();
    console.log('Metrics dashboard initialized');
});
