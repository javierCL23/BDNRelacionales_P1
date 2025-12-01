"""
Script para Cassandra - Almacenamiento histórico
- Carga de datos sintéticos
- Consultas de lectura
"""

from cassandra.cluster import Cluster
from datetime import datetime
import time
import os

# Datos
EVENT_TYPES = ['page_view', 'product_view', 'add_to_cart', 'search']

def connect_cassandra(host='localhost', port=9042):
    """Conectar a Cassandra"""
    try:
        cluster = Cluster([host], port=port)
        session = cluster.connect()
        print(f"✓ Conectado a Cassandra ({host}:{port})")
        return cluster, session
    except Exception as e:
        print(f"✗ Error conectando a Cassandra: {e}")
        return None, None


def run_queries(session):
    """Ejecutar consultas de ejemplo"""
    print("\n" + "="*60)
    print("CONSULTAS DE LECTURA")
    print("="*60)

    # Consulta 1: Eventos de hoy
    hour = 9
    print(f"\n1. Últimos 10 eventos de hoy a las {hour}:00:")
    today = datetime.now().date()
    rows = session.execute(
        "SELECT * FROM events_by_day WHERE event_date = %s  AND event_hour = %s LIMIT 10",
        [today,hour]
    )
    for row in rows:
        print(f"\t {row.event_time.strftime("%Y-%m-%d %H:%M:%S")} -> {row.event_type} en sesión {row.session_id}")


    # Consulta 2: Top N por categoría
    print("\n2. Top productos por categoría:")
    for category in ['Tablets', 'Laptops', 'Audio']: 
        rows = session.execute(
            "SELECT product_name, views FROM products_by_category WHERE category = %s LIMIT 3",
            [category]
        )
        print(f"   {category} (Top 3):")
        for row in rows:
            print(f"\t{row.product_name} -> {row.views} vistas")

    # Consulta 3: Sesiones específicas
    print("\n3. Sesiones específicas de usuario:")
    rows = session.execute(
        "SELECT * FROM user_sessions WHERE session_id=%s",
        ['session_1']
    ) 
    for row in rows:
        print(f"\t {row.total_events} eventos en una sesión desde las {row.start_time.strftime("%Y-%m-%d %H:%M:%S")} hasta las {row.end_time.strftime("%Y-%m-%d %H:%M:%S")}")

    # Consulta 5: Eventos por tipo
    print("\n6. Distribución de eventos por tipo:")
    
    for event_type in EVENT_TYPES:
        rows = session.execute(
            "SELECT COUNT(*) as count FROM events_by_day WHERE event_type = %s ALLOW FILTERING",
            [event_type]
        )
        for row in rows:
            print(f"\t Registrados {row.count} de {event_type}'s")




def main():
    # Conectar
    CASSANDRA_HOST = os.getenv("CASSANDRA_HOST",'localhost')
    cluster = None
    session = None
    for _ in range(10):
        cluster, session = connect_cassandra(CASSANDRA_HOST)
        if session:
            break
        time.sleep(1)
    if not session:
        return
    
    session.set_keyspace("techstore")
    # Ejecutar consultas
    run_queries(session)

    print("\n" + "="*60)
    print("✓ Proceso completado")
    print("="*60 + "\n")

    # Cerrar conexión
    cluster.shutdown()

if __name__ == "__main__":
    main()
