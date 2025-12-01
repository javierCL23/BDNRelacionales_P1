"""
Script para Cassandra - Almacenamiento histórico
- Carga de datos sintéticos
- Consultas de lectura
"""

from cassandra.cluster import Cluster
from datetime import datetime, timedelta
import random
import time
import os

# Datos de productos
PRODUCTS = [
    # Smartphones 
    {"id": 1, "name": "Smartphone Pro X", "category": "Smartphones"},
    {"id": 6, "name": "Smartphone Max 14", "category": "Smartphones"},
    {"id": 7, "name": "Smartphone Lite 5G", "category": "Smartphones"},
    
    # Laptops 
    {"id": 2, "name": "Laptop Ultra 15", "category": "Laptops"},
    {"id": 8, "name": "Laptop Gaming 17", "category": "Laptops"},
    {"id": 9, "name": "Laptop Business 13", "category": "Laptops"},
    
    # Audio 
    {"id": 3, "name": "Auriculares BT Pro", "category": "Audio"},
    {"id": 10, "name": "Auriculares Noise Cancel", "category": "Audio"},
    {"id": 11, "name": "Altavoz Portátil 360", "category": "Audio"},
    
    # Wearables 
    {"id": 4, "name": "Smartwatch Fit", "category": "Wearables"},
    {"id": 12, "name": "Smartwatch Sport GPS", "category": "Wearables"},
    {"id": 13, "name": "Pulsera Actividad Pro", "category": "Wearables"},
    
    # Tablets 
    {"id": 5, "name": "Tablet Pro 12", "category": "Tablets"},
    {"id": 14, "name": "Tablet Air 10", "category": "Tablets"},
    {"id": 15, "name": "Tablet Kids Edition", "category": "Tablets"},
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
        # Tabla 1: Eventos por día (se añade hora para evitar hotspots)
        session.execute("""
            CREATE TABLE IF NOT EXISTS events_by_day (
                event_date date,
                event_hour int,
                event_time timestamp,
                event_type text,
                session_id text,
                product_id int,
                PRIMARY KEY ((event_date,event_hour), event_time)
            ) WITH CLUSTERING ORDER BY (event_time DESC)
        """)

        # Tabla 2: Productos por categoría
        session.execute("""
            CREATE TABLE IF NOT EXISTS products_by_category (
                category text,
                product_id int,
                product_name text,
                views int,
                PRIMARY KEY ((category), product_id)
            ) WITH CLUSTERING ORDER BY (product_id ASC)
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
                session_id text,
                start_time timestamp,
                end_time timestamp,
                total_events int,
                PRIMARY KEY ((session_id), total_events)
            ) WITH CLUSTERING ORDER BY (total_events DESC)
        """)

        print("✓ Tablas creadas")
    except Exception as e:
        print(f"Error creando tablas: {e}")


def generate_synthetic_data(session, num_events=500, num_sessions=100, num_requests=1000):
    """Generar datos sintéticos para todas las tablas"""
    
    print(f"\n{'='*70}")
    print(f"Generando datos sintéticos...")
    print(f"{'='*70}")
    
    # Preparar statements
    insert_event = session.prepare("""
        INSERT INTO events_by_day (event_date, event_hour, event_time, event_type, session_id, product_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    
    insert_product = session.prepare("""
        INSERT INTO products_by_category (category, product_id, product_name, views)
        VALUES (?, ?, ?, ?)
    """)
    
    insert_session = session.prepare("""
        INSERT INTO user_sessions (session_id, start_time, end_time, total_events)
        VALUES (?, ?, ?, ?)
    """)
    
    insert_request = session.prepare("""
        INSERT INTO requests_by_time (date, hour, minute, second, request_count)
        VALUES (?, ?, ?, ?, ?)
    """)
    
    # Diccionario para contar eventos por sesión
    session_event_counts = {f"session_{i+1}": 0 for i in range(num_sessions)}
    
    base_date = datetime.now()
    

    # 1. GENERAR EVENTOS

    print(f"\nGenerando {num_events} eventos:")
    for i in range(1, num_events + 1):
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
        event_hour = event_time.hour
        event_type = random.choice(EVENT_TYPES)
        session_id = f"session_{random.randint(1, num_sessions)}"
        product_id = random.choice([p['id'] for p in PRODUCTS]) if event_type != 'page_view' else None
        
        session.execute(insert_event, (
            event_date, 
            event_hour,
            event_time, 
            event_type, 
            session_id, 
            product_id
        ))
        
        session_event_counts[session_id] += 1
        
        if i % 100 == 0:
            print(f"    Insertados {i}/{num_events} eventos")
    
    print(f"    {num_events} eventos insertados")
    

    # 2. GENERAR PRODUCTOS

    print(f"\nGenerando productos con vistas")
    for product in PRODUCTS:
        views = random.randint(50, 500)
        session.execute(insert_product, (
            product['category'],
            product['id'],
            product['name'],
            views
        ))
    
    print(f"    {len(PRODUCTS)} productos insertados")
    

    # 3. GENERAR SESIONES

    print(f"\nGenerando {num_sessions} sesiones:")
    for session_id, total_events in session_event_counts.items():
        start_time = base_date - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        end_time = start_time + timedelta(minutes=random.randint(1, 120))
        
        session.execute(insert_session, (
            session_id, 
            start_time, 
            end_time, 
            total_events
        ))
    
    print(f"    {num_sessions} sesiones insertadas")
    

    # 4. PETICIONES POR SEGUNDO

    print(f"\nGenerando {num_requests} registros de peticiones:")
    
    # Usar diccionario para acumular peticiones del mismo segundo
    request_map = {}
    
    for _ in range(num_requests):
        random_days = random.randint(0, 7)
        date_time = base_date - timedelta(days=random_days)
        date = date_time.date()
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        key = (date, hour, minute, second)
        request_map[key] = request_map.get(key, 0) + random.randint(1, 20)
    
    # Insertar peticiones acumuladas
    for (date, hour, minute, second), count in request_map.items():
        session.execute(insert_request, (date, hour, minute, second, count))
    
    print(f"    {len(request_map)} registros únicos de peticiones insertados")
    
    print(f"\n{'='*70}")
    print("Datos generados")
    print(f"{'='*70}")



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
            

    # Crear keyspace y tablas
    create_keyspace(session)
    create_tables(session)

    num_records = 500
    generate_synthetic_data(session, num_records)


    # Cerrar conexión
    cluster.shutdown()

if __name__ == "__main__":
    main()
