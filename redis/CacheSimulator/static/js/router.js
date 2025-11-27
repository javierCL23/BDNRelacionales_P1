document.addEventListener('DOMContentLoaded', () => {

    // =========================
    // Redirección al hacer clic en productos
    // =========================
    const productCards = document.querySelectorAll('.product-card');
    productCards.forEach(card => {
        card.addEventListener('click', (e) => {
            // Ignorar si el clic vino de un botón dentro del card
            if (e.target.closest('.btn-add-cart')) return;

            const productId = card.getAttribute('data-product-id');
            if (productId) {
                // Redirigir a la ruta de Flask
                window.location.href = `/products/${productId}`;
            }
        });
    });

    // =========================
    // Hero CTA Button
    // =========================
    const heroCTA = document.getElementById('hero-cta');
    if (heroCTA) {
        heroCTA.addEventListener('click', () => {
            // Por ejemplo, redirige a /products
            window.location.href = '/products';
        });
    }

    // =========================
    // Blog cards (opcional, solo si existen rutas en Flask)
    // =========================
    const blogCards = document.querySelectorAll('.blog-card');
    blogCards.forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('.btn-read-more')) return;

            const articleId = card.getAttribute('data-article-id');
            if (articleId) {
                window.location.href = `/blog/${articleId}`;
            }
        });
    });

});
