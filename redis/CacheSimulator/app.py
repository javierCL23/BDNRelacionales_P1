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

REDIS_LOCAL_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_LOCAL_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_LOCAL_PASSWORD = os.getenv('REDIS_PASSWORD', None)

try:
    redis_cache = rd.Redis(
        host=REDIS_LOCAL_HOST,
        port=REDIS_LOCAL_PORT,
        password=REDIS_LOCAL_PASSWORD,
        decode_responses=True
    )
    redis_cache.ping()
    print(f"✓ Redis Cache conectado ({REDIS_LOCAL_HOST}:{REDIS_LOCAL_PORT})")
except Exception as e:
    print(f"✗ Error conectando a Redis Cache: {e}")
    redis_cache = None

PRODUCTS = [
    {"id": 1, "name": "Smartphone Pro X", "price": 899.0, "category": "Smartphones"},
    {"id": 2, "name": "Laptop Ultra 15\"", "price": 1299.0, "category": "Laptops"},
    {"id": 3, "name": "Auriculares Wireless", "price": 199.0, "category": "Audio"},
    {"id": 4, "name": "Smartwatch Fit", "price": 299.0, "category": "Wearables"},
    {"id": 5, "name": "Cámara Digital 4K", "price": 799.0, "category": "Cámaras"},
    {"id": 6, "name": "Monitor Gaming 27\"", "price": 449.0, "category": "Monitores"},
    {"id": 7, "name": "Teclado Mecánico RGB", "price": 129.0, "category": "Periféricos"},
    {"id": 8, "name": "Ratón Gaming Pro", "price": 79.0, "category": "Periféricos"}
]


def get_from_relational_db_simulated(query_type, **kwargs):
    time.sleep(1)
    if query_type == "all_products":
        return PRODUCTS
    elif query_type == "product_by_id":
        product_id = kwargs.get("product_id")
        return next((p for p in PRODUCTS if p["id"] == product_id), None)
    elif query_type == "products_by_category":
        category = kwargs.get("category")
        return [p for p in PRODUCTS if p["category"] == category]
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products', methods=['GET'])
def get_products():
    try:
        start_time = time.time()
        productos = get_from_relational_db_simulated("all_products")
        lat = (time.time() - start_time) * 1000

        if redis_cache:
            for p in productos:
                redis_cache.set(f"cache:product:{p['id']}", json.dumps(p), ex=60)

        return jsonify({
            'source': 'database',
            'count': len(productos),
            'data': productos,
            'latency_ms': round(lat, 2)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/products/cached', methods=['GET'])
def get_products_cached():
    try:
        start_time = time.time()

        if redis_cache:
            keys = redis_cache.keys("cache:product:*")

            # Si NO hay productos cacheados → devolver lista vacía
            if not keys:
                return jsonify({
                    'source': 'cache',
                    'count': 0,
                    'data': [],
                    'latency_ms': (time.time() - start_time) * 1000
                })

            productos = []
            for k in keys:
                data = redis_cache.get(k)
                if data:
                    p = json.loads(data)
                    productos.append(p)

                    # recargar TTL
                    redis_cache.set(f"cache:product:{p['id']}", json.dumps(p), ex=60)

            return jsonify({
                'source': 'cache',
                'count': len(productos),
                'data': productos,
                'latency_ms': (time.time() - start_time) * 1000
            })

        # Cache no disponible
        return jsonify({'error': 'Cache not available'}), 503

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        cache_key = f"cache:product:{product_id}"
        start_time = time.time()

        if redis_cache:
            cached = redis_cache.get(cache_key)
            if cached:
                return jsonify({
                    'source': 'cache',
                    'data': json.loads(cached),
                    'latency_ms': (time.time() - start_time) * 1000
                })

        product = get_from_relational_db_simulated("product_by_id", product_id=product_id)
        db_latency = (time.time() - start_time) * 1000

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        if redis_cache:
            redis_cache.set(cache_key, json.dumps(product), ex=60)

        return jsonify({
            'source': 'database',
            'data': product,
            'latency_ms': round(db_latency, 2)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cache/stats', methods=['GET'])
def cache_stats():
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

@app.route('/cache/invalidate', methods=['POST'])
def invalidate_cache():
    try:
        if not redis_cache:
            return jsonify({'error': 'Cache not available'}), 503

        data = request.get_json()
        target = data.get('target', 'all')

        if target == 'product':
            product_id = data.get('product_id')
            redis_cache.delete(f'cache:product:{product_id}')
            message = f'Product {product_id} invalidated'
        else:
            return jsonify({'error': 'Invalid target'}), 400

        return jsonify({'status': 'success', 'message': message})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cache/invalidate/<int:product_id>', methods=['GET'])
def invalidate_cache_get(product_id):
    try:
        if not redis_cache:
            return jsonify({'error': 'Cache not available'}), 503

        redis_cache.delete(f'cache:product:{product_id}')

        return jsonify({'status': 'success', 'message': f'Product {product_id} invalidated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("TechStore iniciada")
    app.run(debug=True, host='0.0.0.0', port=5000)
