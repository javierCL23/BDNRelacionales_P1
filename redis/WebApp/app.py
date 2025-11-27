"""
Aplicación web Flask para TechStore
- Redis LOCAL: Eventos en tiempo real
- Redis CLOUD: Caché de productos (patrón Cache-Aside)
- Simulación de BD relacional
"""

from flask import Flask, render_template, request, jsonify
import redis as rd
import time
import os
import json
from datetime import datetime
import random

app = Flask(__name__)

# ==================== CONFIGURACIÓN ====================

# Redis LOCAL - Eventos en tiempo real
REDIS_LOCAL_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_LOCAL_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_LOCAL_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Redis CLOUD - Caché (o mismo local si no hay Cloud configurado)
REDIS_CLOUD_HOST = os.getenv('REDIS_CLOUD_HOST', REDIS_LOCAL_HOST)
REDIS_CLOUD_PORT = int(os.getenv('REDIS_CLOUD_PORT', REDIS_LOCAL_PORT))
REDIS_CLOUD_PASSWORD = os.getenv('REDIS_CLOUD_PASSWORD', REDIS_LOCAL_PASSWORD)

# ==================== CONEXIONES ====================

# Redis LOCAL - Eventos en tiempo real
try:
    redis_local = rd.Redis(
        host=REDIS_LOCAL_HOST,
        port=REDIS_LOCAL_PORT,
        password=REDIS_LOCAL_PASSWORD,
        decode_responses=True
    )
    redis_local.ping()
    print(f"✓ Redis LOCAL conectado ({REDIS_LOCAL_HOST}:{REDIS_LOCAL_PORT})")
except Exception as e:
    print(f"✗ Error conectando a Redis LOCAL: {e}")
    redis_local = None

# Redis CLOUD - Caché
try:
    redis_cache = rd.Redis(
        host=REDIS_CLOUD_HOST,
        port=REDIS_CLOUD_PORT,
        password=REDIS_CLOUD_PASSWORD,
        decode_responses=True
    )
    redis_cache.ping()
    print(f"✓ Redis CLOUD conectado ({REDIS_CLOUD_HOST}:{REDIS_CLOUD_PORT})")
except Exception as e:
    print(f"✗ Error conectando a Redis CLOUD: {e}")
    redis_cache = None

# Datos de productos en memoria (no hay BD real)
PRODUCTS = [
    {"id": 1, "name": "Smartphone Pro X", "price": 899.99, "category": "Smartphones"},
    {"id": 2, "name": "Laptop Ultra 15", "price": 1299.99, "category": "Laptops"},
    {"id": 3, "name": "Auriculares BT Pro", "price": 249.99, "category": "Audio"},
    {"id": 4, "name": "Smartwatch Fit", "price": 199.99, "category": "Wearables"},
    {"id": 5, "name": "Tablet Pro 12", "price": 799.99, "category": "Tablets"},
]

# ==================== FUNCIONES AUXILIARES ====================

def save_to_relational_db_simulated(data):
    """
    Simula guardado en BD relacional (SQLite, PostgreSQL, etc.)
    En realidad no guarda nada, solo hace un sleep para simular latencia
    """
    time.sleep(0.005)  # Simula 5ms de latencia de escritura en BD
    return True

def get_from_relational_db_simulated(query_type, **kwargs):
    """
    Simula lectura de BD relacional
    En realidad devuelve datos hardcodeados con latencia simulada
    """
    time.sleep(0.05)  # Simula 50ms de latencia de lectura en BD

    if query_type == "all_products":
        return PRODUCTS
    elif query_type == "product_by_id":
        product_id = kwargs.get("product_id")
        return next((p for p in PRODUCTS if p["id"] == product_id), None)
    elif query_type == "products_by_category":
        category = kwargs.get("category")
        return [p for p in PRODUCTS if p["category"] == category]

    return None

# ==================== ENDPOINTS - PÁGINAS ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cache-dashboard')
def cache_dashboard():
    return render_template('cache_dashboard.html')

# ==================== ENDPOINTS - TRACKING ====================

@app.route('/api/track', methods=['POST'])
def track_event():
    """
    Recibe eventos del frontend y los guarda en Redis LOCAL
    """
    try:
        event_data = request.get_json()
        if not event_data:
            return jsonify({'error': 'No data provided'}), 400

        event_type = event_data.get('event_type', 'unknown')
        ts = int(time.time())

        if redis_local:
            # Incrementar contador de peticiones
            redis_local.incr(f"requests:{ts}")
            redis_local.expire(f"requests:{ts}", 120)

            # Guardar evento en lista
            event_json = json.dumps({
                'timestamp': ts,
                'type': event_type,
                'data': event_data
            })
            redis_local.lpush(f"events:{event_type}", event_json)
            redis_local.ltrim(f"events:{event_type}", 0, 999)
            redis_local.expire(f"events:{event_type}", 3600)

        return jsonify({
            'status': 'success',
            'event_type': event_type,
            'timestamp': ts
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Métricas en tiempo real"""
    try:
        metrics = {
            'active_users': random.randint(5, 25),
            'requests_per_sec': round(random.uniform(10, 50), 2),
            'cpu_usage': random.uniform(20, 80),
            'avg_latency': round(random.uniform(20, 150), 2),
            'timestamp': int(time.time())
        }
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ENDPOINTS - PRODUCTOS CON CACHÉ ====================

@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Obtener productos con patrón Cache-Aside:
    1. Intentar leer de Redis CLOUD (caché)
    2. Si existe → retornar (HIT)
    3. Si no existe → consultar BD relacional
    4. Guardar en caché
    5. Retornar
    """
    try:
        cache_key = "cache:products:all"

        # Intentar leer de caché
        if redis_cache:
            cached = redis_cache.get(cache_key)
            if cached:
                # CACHE HIT
                return jsonify({
                    'source': 'cache',
                    'count': len(json.loads(cached)),
                    'data': json.loads(cached),
                    'latency_ms': 2
                })

        # CACHE MISS - consultar BD
        start_time = time.time()
        products = get_from_relational_db_simulated("all_products")
        db_latency = (time.time() - start_time) * 1000

        # Guardar en caché (TTL 10 minutos)
        if redis_cache:
            redis_cache.setex(cache_key, 600, json.dumps(products))

        return jsonify({
            'source': 'database',
            'count': len(products),
            'data': products,
            'latency_ms': round(db_latency, 2)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Obtener producto específico con caché"""
    try:
        cache_key = f"cache:product:{product_id}"

        # Intentar caché
        if redis_cache:
            cached = redis_cache.get(cache_key)
            if cached:
                return jsonify({
                    'source': 'cache',
                    'data': json.loads(cached),
                    'latency_ms': 2
                })

        # Consultar BD
        start_time = time.time()
        product = get_from_relational_db_simulated("product_by_id", product_id=product_id)
        db_latency = (time.time() - start_time) * 1000

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Guardar en caché (TTL 30 minutos)
        if redis_cache:
            redis_cache.setex(cache_key, 1800, json.dumps(product))

        return jsonify({
            'source': 'database',
            'data': product,
            'latency_ms': round(db_latency, 2)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ENDPOINTS - ESTADÍSTICAS DE CACHÉ ====================

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Estadísticas de eficiencia de caché"""
    try:
        if not redis_cache:
            return jsonify({'error': 'Cache not available'}), 503

        hits = int(redis_cache.get('cache:stats:hits') or 0)
        misses = int(redis_cache.get('cache:stats:misses') or 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0

        return jsonify({
            'hits': hits,
            'misses': misses,
            'total_requests': total,
            'hit_rate': round(hit_rate, 2),
            'timestamp': int(time.time())
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """Invalidar caché manualmente"""
    try:
        if not redis_cache:
            return jsonify({'error': 'Cache not available'}), 503

        data = request.get_json()
        target = data.get('target', 'all')

        if target == 'all':
            redis_cache.delete('cache:products:all')
            message = 'All cache invalidated'
        elif target == 'product':
            product_id = data.get('product_id')
            redis_cache.delete(f'cache:product:{product_id}')
            message = f'Product {product_id} invalidated'
        else:
            return jsonify({'error': 'Invalid target'}), 400

        return jsonify({'status': 'success', 'message': message})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== STARTUP ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TechStore - Aplicación Web")
    print("="*60)
    print(f"Redis LOCAL (eventos): {REDIS_LOCAL_HOST}:{REDIS_LOCAL_PORT}")
    print(f"Redis CLOUD (caché):   {REDIS_CLOUD_HOST}:{REDIS_CLOUD_PORT}")
    print("BD Relacional:         En memoria")
    print("="*60 + "\n")

    # Pre-calentar caché
    if redis_cache:
        print("Pre-calentando caché...")
        redis_cache.setex("cache:products:all", 600, json.dumps(PRODUCTS))
        for product in PRODUCTS:
            redis_cache.setex(f"cache:product:{product['id']}", 1800, json.dumps(product))
        print("✓ Caché inicializada\n")

    print("✅ Sistema listo\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
