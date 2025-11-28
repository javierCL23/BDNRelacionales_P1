# TechStore - Práctica Redis y Cassandra

Proyecto de Bases de Datos No Relacionales para el Grado en Ciencia e Ingeniería de Datos - URJC 2025/2026

## Descripción del Proyecto

Sistema de comercio electrónico que combina dos tecnologías NoSQL complementarias:

- **Redis**: Para eventos en tiempo real y caché de productos (patrón Cache-Aside)
- **Apache Cassandra**: Para almacenamiento histórico y consultas analíticas

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                  ARQUITECTURA GENERAL                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐       ┌──────────────┐               │
│  │ Redis LOCAL  │       │ Redis CLOUD  │               │
│  │ (Docker)     │       │ (Free Plan)  │               │
│  │              │       │              │               │
│  │ • Caché de   │       │ • Métricas   │               │
│  │   productos  │       │   tiempo real│               │
│  │ • Cache-Aside│       │ • ACLs       │               │
│  │ • Replicación│       │ • requests:* │               │
│  └──────────────┘       └──────────────┘               │
│         ↑                      ↑                        │
│         │                      │                        │
│  ┌──────┴──────────────────────┴──────┐                │
│  │   Aplicación Web Flask             │                │
│  │  • API REST                         │                │
│  │  • Dashboard métricas               │                │
│  │  • Tracking eventos                 │                │
│  └────────────────────────────────────┘                │
│                                                          │
│  ┌──────────────────────────────────┐                  │
│  │    Apache Cassandra              │                  │
│  │  • Histórico de eventos          │                  │
│  │  • Consultas analíticas          │                  │
│  │  • Modelado query-first          │                  │
│  └──────────────────────────────────┘                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Componentes

### Parte A - Redis

#### 1. Redis LOCAL (Docker)
- **Propósito**: Caché de productos para la WebApp
- **Patrón**: Cache-Aside (Lazy Loading)
- **Configuración**:
  - 1 Master (puerto 6379)
  - 2 Réplicas (puertos 6380, 6381)
  - Replicación automática con lag=0
- **TTL**: 1800 segundos (30 minutos)
- **Beneficios**: Reduce latencia de ~1000ms a ~1.4ms (99.86% mejora)

#### 2. Redis CLOUD (Plan Free)
- **Propósito**: Almacenamiento de métricas en tiempo real
- **Estructura**: Strings con claves `requests:{timestamp}`
- **ACLs configurados**: 4 usuarios (admin, metrics_writer, metrics_reader, dashboard_user)
- **Servicios**:
  - **SamplesGenerator**: Genera tráfico simulado, escribe métricas
  - **MetricsGenerator**: Lee métricas, dashboard de velas (OHLC)

#### 3. Alta Disponibilidad
- Replicación Master-Replica
- Failover manual demostrable
- Comandos: `REPLICAOF NO ONE` para promover réplica

### Parte B - Cassandra

#### Modelo de Datos (5 tablas)

1. **events_by_day**
   - Partition key: `event_date`
   - Clustering: `event_time DESC`
   - Uso: Consultas de eventos por día

2. **products_by_category**
   - Partition key: `category`
   - Clustering: `product_id`
   - Uso: Productos agrupados por categoría

3. **requests_by_time**
   - Partition key: `(date, hour)`
   - Clustering: `minute, second`
   - Uso: Análisis temporal de peticiones

4. **user_sessions**
   - Partition key: `session_id`
   - Uso: Seguimiento de sesiones de usuario

5. **top_products_by_day**
   - Partition key: `date`
   - Clustering: `views DESC`
   - Uso: Rankings de productos más vistos

#### Consultas Implementadas

1. Eventos de un día específico
2. Productos por categoría
3. Rango temporal de eventos
4. Top N productos por categoría
5. Sesiones de usuario
6. Distribución de eventos por tipo

## Instalación y Uso

### Requisitos Previos

- Docker y Docker Compose
- Python 3.8+
- Cuenta en Redis Cloud (opcional, puede usar Redis local)

### Inicio Rápido

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd BDNRelacionales_P1

# 2. Levantar servicios con Docker
docker-compose up -d

# 3. Verificar servicios
docker ps

# Deberías ver:
# - redis-master (6379)
# - redis-replica-1 (6380)
# - redis-replica-2 (6381)
# - techstore-webapp (5000)
# - metrics-dashboard (8050)
# - samples-generator
```

### Acceder a los Servicios

- **Aplicación Web**: http://localhost:5000
- **Dashboard de Caché**: http://localhost:5000/cache-dashboard
- **Dashboard de Métricas**: http://localhost:8050

### Configurar Cassandra (Opcional)

```bash
# 1. Levantar Cassandra con Docker
docker run -d --name cassandra -p 9042:9042 cassandra:latest

# 2. Esperar que inicie (1-2 minutos)
docker logs -f cassandra
# Espera hasta ver: "Starting listening for CQL clients"

# 3. Instalar driver Python
cd cassandra
pip install -r requirements.txt

# 4. Ejecutar script
python cassandra_simple.py
# Responder 's' para generar datos
# Indicar número de registros (ej: 500)
```

## Demos y Pruebas

### Demo 1: Caché (Cache Hit vs Miss)

```bash
# Primera petición (MISS - lento)
curl http://localhost:5000/products | jq '.source, .latency_ms'
# Output: "database", ~1000

# Segunda petición (HIT - rápido)
curl http://localhost:5000/products/cached | jq '.source, .latency_ms'
# Output: "cache", 1.41

# Mejora: 99.86% más rápido
```

### Demo 2: Replicación Redis

```bash
# Ver estado de replicación
docker exec redis-master redis-cli -a myredispassword INFO replication

# Escribir dato en master
docker exec redis-master redis-cli -a myredispassword SET test:key "valor"

# Leer desde réplica
docker exec redis-replica-1 redis-cli -a myredispassword GET test:key
# Output: "valor"
```

### Demo 3: Failover Manual

```bash
# 1. Verificar estado inicial
docker exec redis-master redis-cli -a myredispassword INFO replication | grep role

# 2. Simular caída del master
docker stop redis-master

# 3. Promover réplica 1 a master
docker exec redis-replica-1 redis-cli -a myredispassword REPLICAOF NO ONE

# 4. Verificar nuevo rol
docker exec redis-replica-1 redis-cli -a myredispassword INFO replication | grep role
# Output: role:master

# 5. Restaurar (opcional)
docker start redis-master
docker exec redis-replica-1 redis-cli -a myredispassword REPLICAOF redis-master 6379
```

### Demo 4: Consultas Cassandra

```bash
cd cassandra
python cassandra_simple.py

# El script ejecutará:
# 1. Conexión a Cassandra
# 2. Creación de keyspace y tablas
# 3. Inserción de 500 registros
# 4. 6 consultas de ejemplo con tiempos medidos
```

## Estructura del Proyecto

```
.
├── docker-compose.yml          # Orquestación de servicios
├── .gitignore                  # Archivos a ignorar en git
├── BD_NO-RELACIONALES_*.pdf    # PDF de la práctica
├── README.md                   # Este archivo
├── MEMORIA.tex                 # Memoria en LaTeX
├── VERIFICACION_SISTEMA.md     # Verificación completa del sistema
├── CAMBIOS_ACL.md              # Historial de cambios ACL
├── COMANDOS_RAPIDOS.md         # Guía de referencia rápida
├── redis-cloud-acl-setup.sh    # Script verificación ACLs
├── cassandra/
│   ├── schema.cql              # Esquema de tablas
│   ├── cassandra_simple.py     # Script principal
│   └── requirements.txt        # Dependencias
└── redis/
    ├── CacheSimulator/         # Aplicación web (caché)
    │   ├── app.py              # Flask app
    │   ├── requirements.txt
    │   ├── Dockerfile
    │   ├── templates/
    │   │   ├── index.html
    │   │   ├── cache_dashboard.html
    │   │   └── products.html
    │   └── static/
    │       ├── css/
    │       └── js/
    ├── MetricsGenerator/       # Dashboard de velas
    │   ├── getCandles.py
    │   ├── Dockerfile
    │   └── pyproject.toml
    └── SamplesGenerator/       # Generador de métricas
        ├── main.py
        ├── Dockerfile
        └── pyproject.toml
```

## API Endpoints

### Productos (con caché)

```bash
# Obtener todos los productos
GET /api/products

# Obtener producto específico
GET /api/products/{id}

# Response:
{
  "source": "cache" | "database",
  "data": {...},
  "latency_ms": 2.34
}
```

### Tracking de Eventos

```bash
# Enviar evento
POST /api/track
{
  "session_id": "session_123",
  "event_type": "product_view",
  "product_id": 1,
  "timestamp": 1234567890
}
```

### Gestión de Caché

```bash
# Estadísticas de caché
GET /api/cache/stats

# Invalidar caché
POST /api/cache/invalidate
{
  "target": "all" | "product",
  "product_id": 1  # si target=product
}
```

### Métricas

```bash
# Métricas en tiempo real
GET /api/metrics

# Response:
{
  "active_users": 15,
  "requests_per_sec": 45.2,
  "cpu_usage": 32.5,
  "avg_latency": 87.3,
  "timestamp": 1234567890
}
```

## Configuración de Redis Cloud

### Paso 1: Crear Cuenta

1. Ir a https://redis.com/try-free/
2. Crear cuenta gratuita
3. Crear base de datos FREE

### Paso 2: Obtener Credenciales

Anotar:
- Host: `redis-xxxxx.cloud.redislabs.com`
- Port: `12345`
- Password: `tu_password`

### Paso 3: Configurar ACLs

**IMPORTANTE**: En Redis Cloud Free, los ACLs se configuran desde la interfaz web, no por CLI.

Crear 4 usuarios desde la web de Redis Cloud:

| Usuario | Password | Permisos |
|---------|----------|----------|
| `admin` | `Admin_techstore_2025` | Todos los comandos |
| `metrics_writer` | `Metrics_writer_pass_2025` | SET, INCR en requests:* |
| `metrics_reader` | `Metrics_reader_pass_2025` | GET, KEYS en requests:* |
| `dashboard_user` | `Dashboard_user_pass_2025` | Solo lectura global |

Verificar desde CLI:

```bash
redis-cli -h redis-15381.c92.us-east-1-3.ec2.cloud.redislabs.com \
          -p 15381 \
          --user admin \
          --pass Admin_techstore_2025 \
          ACL LIST
```

### Paso 4: Actualizar docker-compose.yml

```yaml
services:
  metrics-dashboard:
    environment:
      - REDIS_CLOUD_HOST=redis-15381.c92.us-east-1-3.ec2.cloud.redislabs.com
      - REDIS_CLOUD_PORT=15381
      - REDIS_CLOUD_USER=metrics_reader
      - REDIS_CLOUD_PASSWORD=Metrics_reader_pass_2025

  samples-generator:
    environment:
      - REDIS_CLOUD_HOST=redis-15381.c92.us-east-1-3.ec2.cloud.redislabs.com
      - REDIS_CLOUD_PORT=15381
      - REDIS_CLOUD_USER=metrics_writer
      - REDIS_CLOUD_PASSWORD=Metrics_writer_pass_2025
```

## Observabilidad con Redis Insight

### Instalación

1. Descargar: https://redis.io/insight/
2. Instalar en tu sistema

### Conexión

1. Abrir Redis Insight
2. Agregar conexión LOCAL:
   - **Nombre**: Redis LOCAL Master
   - **Host**: localhost
   - **Port**: 6379
   - **Password**: myredispassword

3. Agregar conexión CLOUD:
   - **Nombre**: Redis CLOUD TechStore
   - **Host**: redis-15381.c92.us-east-1-3.ec2.cloud.redislabs.com
   - **Port**: 15381
   - **Username**: dashboard_user
   - **Password**: Dashboard_user_pass_2025

### Funcionalidades a Explorar

- **Browser**:
  - LOCAL: Explorar claves `cache:product:*`
  - CLOUD: Explorar claves `requests:*`
- **Workbench**:
  - LOCAL: `INFO replication` para ver estado de réplicas
  - CLOUD: `ACL LIST` para ver usuarios configurados
- **Profiler**: Ver comandos GET/SET en tiempo real mientras usas la WebApp
- **Analysis**: Analizar uso de memoria por tipo de dato

## Solución de Problemas

### Error: "Cannot connect to Docker daemon"

```bash
# Iniciar Docker
sudo systemctl start docker

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### Error: "Port 5000 already in use"

```bash
# Ver qué proceso usa el puerto
sudo lsof -i :5000

# Matar el proceso
sudo kill -9 <PID>

# O cambiar puerto en docker-compose.yml
```

### Error: "redis-cli: command not found"

```bash
# El comando debe ejecutarse DENTRO del contenedor
docker exec redis-master redis-cli -a myredispassword <comando>
```

### Cassandra tarda en iniciar

Es normal. Espera 1-2 minutos viendo los logs:

```bash
docker logs -f cassandra
# Espera: "Starting listening for CQL clients"
```

### WebApp no responde

```bash
# Ver logs
docker logs techstore-webapp

# Reconstruir
docker-compose up --build webapp
```

## Comandos Útiles

### Docker

```bash
# Ver todos los contenedores
docker ps -a

# Ver logs de un servicio
docker logs <container_name>
docker logs -f <container_name>  # Seguir en tiempo real

# Reiniciar un servicio
docker restart <container_name>

# Entrar en un contenedor
docker exec -it <container_name> /bin/sh

# Ver uso de recursos
docker stats
```

### Redis

```bash
# Conectar a Redis master
docker exec -it redis-master redis-cli -a myredispassword

# Comandos básicos
PING
INFO
KEYS *
GET key
SET key value
DEL key
TTL key

# Ver replicación
INFO replication

# Ver memoria
INFO memory
```

### Cassandra

```bash
# Conectar a Cassandra
docker exec -it cassandra cqlsh

# Comandos básicos
DESCRIBE KEYSPACES;
USE techstore;
DESCRIBE TABLES;
SELECT * FROM events_by_day LIMIT 10;
```

## Detener Todo

```bash
# Detener servicios de Redis y WebApp
docker-compose down

# Detener Cassandra
docker stop cassandra
docker rm cassandra

# Eliminar volúmenes (CUIDADO: borra datos)
docker volume prune
```

## Equipo

- **Javier**: SamplesGenerator, MetricsGenerator, Dashboard de métricas en tiempo real
- **Miguel**: WebApp, integración Redis caché, Cassandra, documentación

## Requisitos Cumplidos

### Parte A - Redis (100%)

- ✅ Dos despliegues distintos (LOCAL Docker + CLOUD)
- ✅ Roles diferenciados y justificados
- ✅ Replicación (1 master + 2 réplicas)
- ✅ Failover manual demostrable
- ✅ Patrón tiempo real (eventos)
- ✅ Patrón caché (Cache-Aside)
- ✅ Observabilidad con Redis Insight
- ✅ ACLs (4 usuarios, 4 roles)

### Parte B - Cassandra (100%)

- ✅ Despliegue de un nodo
- ✅ Dataset sintético (≥500 registros)
- ✅ Keyspace con estrategia de replicación
- ✅ 5 tablas orientadas a lectura
- ✅ Partition keys documentadas
- ✅ 6 consultas con tiempos medidos

## Tecnologías Utilizadas

- Python 3.12
- Flask 3.0
- Redis 7.0
- Apache Cassandra 4.x
- Docker & Docker Compose
- Dash (para dashboard de métricas)

## Licencia

Proyecto académico - Universidad Rey Juan Carlos 2025/2026
