"""
Aplicación web Flask para simulación de eventos en tiempo real
Envía métricas a Redis para análisis con el sistema de tu compañero
"""

from flask import Flask, render_template, request, jsonify
import redis as rd
import time
import os
import json
from datetime import datetime
import psutil
import random
from collections import defaultdict

app = Flask(__name__)

# Configuración de Redis (desde variables de entorno o defaults)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Estadísticas en memoria para métricas
active_sessions = set()
event_counter = defaultdict(int)
last_request_time = time.time()
request_timestamps = []


def connect_redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD):
    """
    Conecta a Redis, compatible con el código de tu compañero
    """
    try:
        r = rd.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
        r.ping()
        return r
    except rd.ConnectionError as e:
        print(f"Error conectando a Redis: {e}")
        return None


# Conexión global a Redis
redis_client = connect_redis()


def send_event_to_redis(event_type, event_data):
    """
    Envía eventos a Redis siguiendo el esquema de tu compañero
    Usa el mismo patrón: requests:{timestamp}
    """
    if not redis_client:
        return False

    try:
        ts = int(time.time())

        # Incrementar contador de peticiones (compatible con SamplesGenerator)
        key = f"requests:{ts}"
        redis_client.incr(key)
        redis_client.expire(key, 120)  # TTL de 120 segundos

        # Guardar evento detallado en una lista
        event_key = f"events:{event_type}"
        event_json = json.dumps({
            'timestamp': ts,
            'data': event_data
        })
        redis_client.lpush(event_key, event_json)
        redis_client.ltrim(event_key, 0, 999)  # Mantener últimos 1000 eventos
        redis_client.expire(event_key, 3600)  # TTL de 1 hora

        # Métricas agregadas
        redis_client.incr(f"metrics:total_events:{event_type}")
        redis_client.incr("metrics:total_requests")

        return True
    except Exception as e:
        print(f"Error enviando evento a Redis: {e}")
        return False


def update_active_users(session_id):
    """
    Actualiza el conteo de usuarios activos
    """
    active_sessions.add(session_id)
    if redis_client:
        redis_client.sadd("active_sessions", session_id)
        redis_client.expire("active_sessions", 60)  # Expire en 60 segundos


def calculate_requests_per_second():
    """
    Calcula peticiones por segundo basándose en ventana temporal
    """
    global request_timestamps
    current_time = time.time()

    # Filtrar timestamps de los últimos 5 segundos
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < 5]
    request_timestamps.append(current_time)

    # Calcular promedio de peticiones por segundo
    if len(request_timestamps) > 1:
        time_window = request_timestamps[-1] - request_timestamps[0]
        if time_window > 0:
            return len(request_timestamps) / time_window
    return 0


@app.route('/')
def index():
    """
    Página principal de la tienda
    """
    return render_template('index.html')


@app.route('/api/track', methods=['POST'])
def track_event():
    """
    Endpoint para recibir eventos del frontend
    """
    try:
        event_data = request.get_json()

        if not event_data:
            return jsonify({'error': 'No data provided'}), 400

        event_type = event_data.get('event_type', 'unknown')
        session_id = event_data.get('session_id', 'unknown')

        # Actualizar sesiones activas
        update_active_users(session_id)

        # Incrementar contador de eventos
        event_counter[event_type] += 1

        # Enviar a Redis
        send_event_to_redis(event_type, event_data)

        # Calcular RPS
        calculate_requests_per_second()

        return jsonify({
            'status': 'success',
            'event_type': event_type,
            'timestamp': int(time.time())
        })

    except Exception as e:
        print(f"Error procesando evento: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """
    Endpoint para obtener métricas en tiempo real
    """
    try:
        # Obtener usuarios activos de Redis
        active_users = 0
        if redis_client:
            active_users = redis_client.scard("active_sessions") or 0

        # Calcular peticiones por segundo
        rps = calculate_requests_per_second()

        # Obtener uso de CPU
        cpu_usage = psutil.cpu_percent(interval=0.1)

        # Simular latencia (podría calcularse de forma real midiendo tiempos de respuesta)
        avg_latency = random.uniform(20, 150)

        # Si hay mucha carga, aumentar latencia
        if rps > 10:
            avg_latency += random.uniform(50, 200)
        if cpu_usage > 70:
            avg_latency += random.uniform(100, 300)

        metrics = {
            'active_users': active_users,
            'requests_per_sec': round(rps, 2),
            'cpu_usage': cpu_usage,
            'avg_latency': avg_latency,
            'timestamp': int(time.time())
        }

        # Guardar métricas en Redis
        if redis_client:
            redis_client.set('metrics:latest', json.dumps(metrics), ex=60)

        return jsonify(metrics)

    except Exception as e:
        print(f"Error obteniendo métricas: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Estadísticas generales de la aplicación
    """
    try:
        stats = {
            'event_counts': dict(event_counter),
            'active_sessions_count': len(active_sessions),
            'uptime': int(time.time() - app.start_time)
        }

        if redis_client:
            total_requests = redis_client.get("metrics:total_requests")
            stats['total_requests'] = int(total_requests) if total_requests else 0

        return jsonify(stats)

    except Exception as e:
        print(f"Error obteniendo stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.before_request
def before_request():
    """
    Middleware para tracking de peticiones
    """
    request.start_time = time.time()


@app.after_request
def after_request(response):
    """
    Middleware post-request para métricas
    """
    if hasattr(request, 'start_time'):
        latency = (time.time() - request.start_time) * 1000  # en ms

        # Guardar latencia en Redis para análisis
        if redis_client and request.endpoint not in ['static']:
            redis_client.lpush('metrics:latencies', latency)
            redis_client.ltrim('metrics:latencies', 0, 999)
            redis_client.expire('metrics:latencies', 3600)

    return response


if __name__ == '__main__':
    # Timestamp de inicio de la aplicación
    app.start_time = time.time()

    # Verificar conexión a Redis
    if redis_client:
        print("✓ Conectado a Redis correctamente")
    else:
        print("✗ No se pudo conectar a Redis - Verifica que esté corriendo")

    # Iniciar servidor
    print("\n" + "="*50)
    print("🚀 Iniciando TechStore Web Application")
    print("="*50)
    print(f"📊 Dashboard disponible en: http://localhost:5000")
    print(f"🔴 Redis Host: {REDIS_HOST}:{REDIS_PORT}")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
