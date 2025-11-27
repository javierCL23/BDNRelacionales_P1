-- Esquema simple para Cassandra (Parte B de la práctica)
-- Keyspace con estrategia de replicación simple

CREATE KEYSPACE IF NOT EXISTS techstore
    WITH replication = {
        'class': 'SimpleStrategy',
        'replication_factor': 1
    };

USE techstore;

-- Tabla 1: Eventos por día (partition key = fecha)
CREATE TABLE IF NOT EXISTS events_by_day (
    event_date date,
    event_time timestamp,
    event_type text,
    session_id text,
    product_id int,
    PRIMARY KEY (event_date, event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);

-- Tabla 2: Productos más vistos por categoría
CREATE TABLE IF NOT EXISTS products_by_category (
    category text,
    product_id int,
    product_name text,
    view_count counter,
    PRIMARY KEY (category, product_id)
);

-- Tabla 3: Peticiones por segundo (para análisis temporal)
CREATE TABLE IF NOT EXISTS requests_by_time (
    date date,
    hour int,
    minute int,
    second int,
    request_count int,
    PRIMARY KEY ((date, hour), minute, second)
) WITH CLUSTERING ORDER BY (minute ASC, second ASC);

-- Tabla 4: Sesiones de usuario
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id text PRIMARY KEY,
    start_time timestamp,
    end_time timestamp,
    total_events int,
    last_product_viewed int
);

-- Tabla 5: Top productos por día
CREATE TABLE IF NOT EXISTS top_products_by_day (
    date date,
    product_id int,
    product_name text,
    views int,
    PRIMARY KEY (date, views, product_id)
) WITH CLUSTERING ORDER BY (views DESC, product_id ASC);
