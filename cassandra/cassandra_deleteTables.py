from cassandra.cluster import Cluster


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
    
def drop_all_tables(session,cluster):
    """borrar todas las tablas del keyspace techstore"""
    

    # Lista de tablas a borrar
    tables = [
        'events_by_day',
        'products_by_category',
        'requests_by_time',
        'user_sessions'
    ]
    
    # Borrar cada tabla
    print("Borrando tablas...\n")
    for table in tables:
        try:
            session.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  ✓ Tabla '{table}' borrada")
        except Exception as e:
            print(f"  ✗ Error borrando '{table}': {e}")
    
    print("\n" + "="*70)
    print("✅ Proceso completado")
    
    # Cerrar conexión
    cluster.shutdown()
    


if __name__ == "__main__":
    cluster,session = connect_cassandra()
    session.set_keyspace("techstore")
    if session != None:
        drop_all_tables(session,cluster)
    print("Todas las tablas de Cassandra borradas con éxito")