"""
Script para Cassandra - Almacenamiento histórico
- Carga de datos sintéticos
- Consultas de lectura
"""

from cassandra.cluster import Cluster
from datetime import datetime, timedelta
import random
import time

# Datos de productos
PRODUCTS = [
    {"id": 1, "name": "Smartphone Pro X", "category": "Smartphones"},
    {"id": 2, "name": "Laptop Ultra 15", "category": "Laptops"},
    {"id": 3, "name": "Auriculares BT Pro", "category": "Audio"},
    {"id": 4, "name": "Smartwatch Fit", "category": "Wearables"},
    {"id": 5, "name": "Tablet Pro 12", "category": "Tablets"},
]

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

def create_keyspace(session):
    """Crear keyspace"""
    try:
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS techstore
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        session.set_keyspace('techstore')
        print("✓ Keyspace 'techstore' creado/conectado")
    except Exception as e:
        print(f"Error creando keyspace: {e}")

def create_tables(session):
    """Crear tablas"""
    try:
        # Tabla 1: Eventos por día
        session.execute("""
            CREATE TABLE IF NOT EXISTS events_by_day (
                event_date date,
                event_time timestamp,
                event_type text,
                session_id text,
                product_id int,
                PRIMARY KEY (event_date, event_time)
            ) WITH CLUSTERING ORDER BY (event_time DESC)
        """)

        # Tabla 2: Productos por categoría
        session.execute("""
            CREATE TABLE IF NOT EXISTS products_by_category (
                category text,
                product_id int,
                product_name text,
                views int,
                PRIMARY KEY (category, product_id)
            )
        """)

        # Tabla 3: Peticiones por segundo
        session.execute("""
            CREATE TABLE IF NOT EXISTS requests_by_time (
                date date,
                hour int,
                minute int,
                second int,
                request_count int,
                PRIMARY KEY ((date, hour), minute, second)
            ) WITH CLUSTERING ORDER BY (minute ASC, second ASC)
        """)

        # Tabla 4: Sesiones
        session.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id text PRIMARY KEY,
                start_time timestamp,
                end_time timestamp,
                total_events int,
                last_product_viewed int
            )
        """)

        print("✓ Tablas creadas")
    except Exception as e:
        print(f"Error creando tablas: {e}")

def generate_synthetic_data(session, num_records=500):
    """Generar datos sintéticos"""
    print(f"\nGenerando {num_records} registros sintéticos...")

    # Preparar statements
    insert_event = session.prepare("""
        INSERT INTO events_by_day (event_date, event_time, event_type, session_id, product_id)
        VALUES (?, ?, ?, ?, ?)
    """)

    insert_product = session.prepare("""
        INSERT INTO products_by_category (category, product_id, product_name, views)
        VALUES (?, ?, ?, ?)
    """)

    # Generar eventos de los últimos 7 días
    base_date = datetime.now()
    for i in range(num_records):
        # Fecha/hora aleatoria de los últimos 7 días
        random_days = random.randint(0, 7)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        random_seconds = random.randint(0, 59)

        event_time = base_date - timedelta(
            days=random_days,
            hours=random_hours,
            minutes=random_minutes,
            seconds=random_seconds
        )

        event_date = event_time.date()
        event_type = random.choice(EVENT_TYPES)
        session_id = f"session_{random.randint(1, 100)}"
        product_id = random.choice([p['id'] for p in PRODUCTS]) if event_type == 'product_view' else None

        # Insertar evento
        session.execute(insert_event, (event_date, event_time, event_type, session_id, product_id))

        if i % 100 == 0:
            print(f"  Insertados {i} registros...")

    # Insertar productos con contadores de vistas
    for product in PRODUCTS:
        views = random.randint(50, 500)
        session.execute(insert_product, (
            product['category'],
            product['id'],
            product['name'],
            views
        ))

    print(f"✓ {num_records} registros insertados")

def run_queries(session):
    """Ejecutar consultas de ejemplo"""
    print("\n" + "="*60)
    print("CONSULTAS DE LECTURA")
    print("="*60)

    # Consulta 1: Eventos de hoy
    print("\n1. Eventos de hoy:")
    today = datetime.now().date()
    start = time.time()
    rows = session.execute(
        "SELECT * FROM events_by_day WHERE event_date = %s LIMIT 10",
        [today]
    )
    elapsed = (time.time() - start) * 1000
    count = 0
    for row in rows:
        print(f"   {row.event_time.strftime('%H:%M:%S')} - {row.event_type}")
        count += 1
    print(f"   Tiempo: {elapsed:.2f}ms, Registros: {count}")

    # Consulta 2: Productos por categoría
    print("\n2. Productos en categoría 'Smartphones':")
    start = time.time()
    rows = session.execute(
        "SELECT * FROM products_by_category WHERE category = 'Smartphones'"
    )
    elapsed = (time.time() - start) * 1000
    for row in rows:
        print(f"   {row.product_name}: {row.views} vistas")
    print(f"   Tiempo: {elapsed:.2f}ms")

    # Consulta 3: Rango temporal
    print("\n3. Eventos entre fechas:")
    yesterday = today - timedelta(days=1)
    start = time.time()
    rows = session.execute(
        "SELECT COUNT(*) FROM events_by_day WHERE event_date >= %s AND event_date <= %s",
        [yesterday, today]
    )
    elapsed = (time.time() - start) * 1000
    for row in rows:
        print(f"   Total eventos: {row.count}")
    print(f"   Tiempo: {elapsed:.2f}ms")

    # Consulta 4: Top N por categoría
    print("\n4. Top productos por categoría:")
    for category in ['Smartphones', 'Laptops', 'Audio']:
        start = time.time()
        rows = session.execute(
            "SELECT product_name, views FROM products_by_category WHERE category = %s LIMIT 3",
            [category]
        )
        elapsed = (time.time() - start) * 1000
        print(f"   {category} (Top 3):")
        for row in rows:
            print(f"     - {row.product_name}: {row.views} vistas")
        print(f"   Tiempo: {elapsed:.2f}ms")

    # Consulta 5: Sesiones específicas
    print("\n5. Sesiones de usuario:")
    start = time.time()
    rows = session.execute("SELECT * FROM user_sessions LIMIT 5")
    elapsed = (time.time() - start) * 1000
    count = 0
    for row in rows:
        print(f"   {row.session_id}: {row.total_events} eventos")
        count += 1
    print(f"   Tiempo: {elapsed:.2f}ms, Registros: {count}")

    # Consulta 6: Eventos por tipo
    print("\n6. Distribución de eventos por tipo:")
    start = time.time()
    for event_type in EVENT_TYPES:
        rows = session.execute(
            "SELECT COUNT(*) as count FROM events_by_day WHERE event_type = %s ALLOW FILTERING",
            [event_type]
        )
        for row in rows:
            print(f"   {event_type}: {row.count}")
    elapsed = (time.time() - start) * 1000
    print(f"   Tiempo: {elapsed:.2f}ms")

def main():
    print("\n" + "="*60)
    print("CASSANDRA - PARTE B DE LA PRÁCTICA")
    print("="*60)

    # Conectar
    cluster, session = connect_cassandra()
    if not session:
        return

    # Crear keyspace y tablas
    create_keyspace(session)
    create_tables(session)

    # Preguntar si generar datos
    print("\n¿Generar datos sintéticos? (s/n): ", end='')
    response = input().lower()

    if response == 's':
        num_records = int(input("Número de registros (por defecto 500): ") or "500")
        generate_synthetic_data(session, num_records)

    # Ejecutar consultas
    run_queries(session)

    print("\n" + "="*60)
    print("✓ Proceso completado")
    print("="*60 + "\n")

    # Cerrar conexión
    cluster.shutdown()

if __name__ == "__main__":
    main()
