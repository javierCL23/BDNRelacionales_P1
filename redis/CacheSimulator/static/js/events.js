// Sistema de captura de eventos para análisis en tiempo real

class EventTracker {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.pageLoadTime = Date.now();
        this.events = [];
        this.initializeTracking();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async sendEvent(eventType, eventData) {
        const event = {
            session_id: this.sessionId,
            event_type: eventType,
            timestamp: Date.now(),
            page_url: window.location.pathname,
            user_agent: navigator.userAgent,
            screen_width: window.screen.width,
            screen_height: window.screen.height,
            ...eventData
        };

        try {
            await fetch('/api/track', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(event)
            });
        } catch (error) {
            console.error('Error sending event:', error);
        }
    }

    initializeTracking() {
        // Page view tracking
        this.sendEvent('page_view', {
            referrer: document.referrer,
            time_on_load: Date.now() - this.pageLoadTime
        });

        // Click tracking en productos
        document.querySelectorAll('.product-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const productId = card.dataset.productId;
                const productName = card.querySelector('h3').textContent;
                this.sendEvent('product_view', {
                    product_id: productId,
                    product_name: productName
                });
            });
        });

        // Click tracking en botones "Añadir al carrito"
        document.querySelectorAll('.btn-add-cart').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const card = e.target.closest('.product-card');
                const productId = card.dataset.productId;
                const productName = card.querySelector('h3').textContent;
                const price = card.querySelector('.price').textContent;

                this.sendEvent('add_to_cart', {
                    product_id: productId,
                    product_name: productName,
                    price: price
                });

                // Feedback visual
                btn.textContent = '✓ Añadido';
                btn.style.background = '#28a745';
                setTimeout(() => {
                    btn.textContent = 'Añadir al carrito';
                    btn.style.background = '';
                }, 2000);
            });
        });

        // Click tracking en artículos del blog
        document.querySelectorAll('.blog-card').forEach(card => {
            const readMoreBtn = card.querySelector('.btn-read-more');
            readMoreBtn.addEventListener('click', () => {
                const articleId = card.dataset.articleId;
                const articleTitle = card.querySelector('h3').textContent;
                this.sendEvent('article_read', {
                    article_id: articleId,
                    article_title: articleTitle
                });
            });
        });

        // Search tracking
        const searchBtn = document.getElementById('search-btn');
        const searchInput = document.getElementById('search-input');

        searchBtn.addEventListener('click', () => {
            const query = searchInput.value;
            if (query.trim()) {
                this.sendEvent('search', {
                    query: query,
                    results_count: Math.floor(Math.random() * 20)
                });
            }
        });

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && searchInput.value.trim()) {
                this.sendEvent('search', {
                    query: searchInput.value,
                    results_count: Math.floor(Math.random() * 20)
                });
            }
        });

        // Navigation tracking
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const page = link.dataset.page;
                this.sendEvent('navigation', {
                    target_page: page,
                    from_page: 'home'
                });
            });
        });

        // CTA Button tracking
        const ctaBtn = document.getElementById('hero-cta');
        if (ctaBtn) {
            ctaBtn.addEventListener('click', () => {
                this.sendEvent('cta_click', {
                    cta_location: 'hero_section',
                    cta_text: 'Ver Ofertas'
                });
            });
        }

        // Scroll depth tracking
        let maxScroll = 0;
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            const scrollPercentage = Math.round(
                (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100
            );

            if (scrollPercentage > maxScroll) {
                maxScroll = scrollPercentage;

                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    this.sendEvent('scroll_depth', {
                        depth_percentage: maxScroll
                    });
                }, 500);
            }
        });

        // Time on page tracking (enviar cada 30 segundos)
        setInterval(() => {
            const timeOnPage = Math.round((Date.now() - this.pageLoadTime) / 1000);
            this.sendEvent('time_on_page', {
                seconds: timeOnPage
            });
        }, 30000);

        // Page exit tracking
        window.addEventListener('beforeunload', () => {
            const timeOnPage = Math.round((Date.now() - this.pageLoadTime) / 1000);
            this.sendEvent('page_exit', {
                total_time: timeOnPage
            });
        });

        // Visibility tracking (tab switching)
        document.addEventListener('visibilitychange', () => {
            this.sendEvent('visibility_change', {
                is_visible: !document.hidden
            });
        });
    }
}

// Inicializar tracker cuando la página cargue
document.addEventListener('DOMContentLoaded', () => {
    window.eventTracker = new EventTracker();
    console.log('Event tracking initialized');
});
