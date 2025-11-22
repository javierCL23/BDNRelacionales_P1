#!/bin/bash

# Script de inicio rápido para el proyecto BDNR
# Universidad Rey Juan Carlos - 2025/2026
# Sistema completo: Redis LOCAL + Redis CLOUD (caché) + SQLite + [Cassandra]

echo "======================================================="
echo "🚀 PROYECTO BDNR - REDIS & CASSANDRA"
echo "======================================================="
echo "   Sistema de TechStore con Arquitectura de 3 Capas"
echo "   - Redis LOCAL:  Eventos tiempo real"
echo "   - Redis CLOUD:  Caché de productos (Cache-Aside)"
echo "   - SQLite:       Base de datos tradicional"
echo "   - Cassandra:    Histórico (Parte B)"
echo "======================================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo -e "${CYAN}$1${NC}"
}

print_highlight() {
    echo -e "${PURPLE}➜${NC} $1"
}

# Verificar Docker
print_info "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado"
    echo "Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker instalado"

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose no está instalado"
    exit 1
fi
print_success "Docker Compose instalado"

echo ""
echo "======================================================="
echo "📋 MENÚ PRINCIPAL"
echo "======================================================="
echo ""
echo "🚀 INICIO RÁPIDO:"
echo "  1. Iniciar sistema completo (Docker Compose)"
echo "  2. Iniciar con CACHÉ activada (app_with_cache.py)"
echo ""
echo "🔧 GESTIÓN DE SERVICIOS:"
echo "  3. Ver estado de servicios"
echo "  4. Ver logs en tiempo real"
echo "  5. Detener todos los servicios"
echo "  6. Limpiar y reiniciar desde cero"
echo ""
echo "🧪 TESTING Y DEMOS:"
echo "  7. Probar conectividad completa"
echo "  8. Test de caché (MISS → HIT)"
echo "  9. Pre-calentar caché"
echo "  10. Ejecutar simulador de tráfico"
echo ""
echo "📊 INFORMACIÓN:"
echo "  11. Ver URLs de servicios"
echo "  12. Estadísticas de caché"
echo "  13. Verificar replicación Redis"
echo ""
echo "⚙️ CONFIGURACIÓN:"
echo "  14. Configurar Redis Cloud (guía)"
echo "  15. Iniciar solo Redis local"
echo "  16. Iniciar solo webapp (sin Docker)"
echo ""
echo "  0. Salir"
echo ""

read -p "Selecciona una opción [0-16]: " option

case $option in
    1)
        print_header "======================================================="
        print_header "🚀 INICIANDO SISTEMA COMPLETO CON DOCKER COMPOSE"
        print_header "======================================================="
        echo ""

        print_info "Levantando servicios..."
        docker-compose up -d

        # Esperar a que los servicios estén listos
        print_info "Esperando a que los servicios estén listos..."
        sleep 5

        echo ""
        print_success "✨ Sistema iniciado correctamente"
        echo ""
        echo "======================================================="
        echo "🌐 SERVICIOS DISPONIBLES"
        echo "======================================================="
        echo ""
        echo "  📱 Aplicación Web TechStore:"
        echo -e "     ${GREEN}http://localhost:5000${NC}"
        echo ""
        echo "  ⚡ Dashboard de Caché (NUEVO):"
        echo -e "     ${GREEN}http://localhost:5000/cache-dashboard${NC}"
        echo ""
        echo "  📊 Dashboard de Métricas (Velas):"
        echo -e "     ${GREEN}http://localhost:8050${NC}"
        echo ""
        echo "  🔴 Redis Master (eventos tiempo real):"
        echo -e "     ${GREEN}localhost:6379${NC}"
        echo "     Password: myredispassword"
        echo ""
        echo "  🔴 Redis Replica 1:"
        echo -e "     ${GREEN}localhost:6380${NC}"
        echo ""
        echo "  🔴 Redis Replica 2:"
        echo -e "     ${GREEN}localhost:6381${NC}"
        echo ""
        echo "======================================================="
        echo ""
        print_highlight "Próximos pasos sugeridos:"
        echo "  1. Abrir http://localhost:5000 en tu navegador"
        echo "  2. Abrir http://localhost:5000/cache-dashboard"
        echo "  3. Ejecutar opción 8 para probar la caché"
        echo "  4. Ejecutar opción 10 para generar tráfico"
        echo ""
        print_info "Para ver logs: docker-compose logs -f"
        print_info "Para detener: docker-compose down"
        ;;

    2)
        print_header "======================================================="
        print_header "⚡ INICIANDO CON SISTEMA DE CACHÉ ACTIVADO"
        print_header "======================================================="
        echo ""

        print_info "Verificando que Redis está corriendo..."
        if ! docker ps | grep -q redis-master; then
            print_warning "Redis no está corriendo, iniciándolo..."
            docker-compose up -d redis-master redis-replica-1 redis-replica-2
            sleep 3
        fi
        print_success "Redis OK"

        cd redis/WebApp

        # Verificar si existe venv
        if [ ! -d "venv" ]; then
            print_info "Creando entorno virtual..."
            python3 -m venv venv
        fi

        source venv/bin/activate

        # Instalar dependencias
        print_info "Instalando dependencias..."
        pip install -q -r requirements.txt

        # Verificar archivos necesarios
        if [ ! -f "database.py" ]; then
            print_error "Archivo database.py no encontrado"
            exit 1
        fi

        if [ ! -f "cache.py" ]; then
            print_error "Archivo cache.py no encontrado"
            exit 1
        fi

        if [ ! -f "app_with_cache.py" ]; then
            print_error "Archivo app_with_cache.py no encontrado"
            exit 1
        fi

        print_success "Todos los archivos presentes"

        # Configurar variables de entorno para Redis
        export REDIS_HOST=localhost
        export REDIS_PORT=6379
        export REDIS_PASSWORD=myredispassword
        export REDIS_CLOUD_HOST=localhost
        export REDIS_CLOUD_PORT=6379
        export REDIS_CLOUD_PASSWORD=myredispassword

        # Iniciar aplicación con caché
        echo ""
        print_success "🔥 Iniciando servidor Flask con CACHÉ activada..."
        echo ""
        print_highlight "URLs disponibles:"
        echo "  - Webapp: http://localhost:5000"
        echo "  - Dashboard Caché: http://localhost:5000/cache-dashboard"
        echo ""

        python app_with_cache.py
        ;;

    3)
        print_header "======================================================="
        print_header "📊 ESTADO DE SERVICIOS"
        print_header "======================================================="
        echo ""

        print_info "Servicios Docker:"
        echo ""
        docker-compose ps
        echo ""

        print_info "Verificando conectividad..."
        echo ""

        # Test Redis Master
        if docker exec redis-master redis-cli -a myredispassword ping &> /dev/null; then
            print_success "Redis Master: ACTIVO"
        else
            print_error "Redis Master: INACTIVO"
        fi

        # Test Redis Replica 1
        if docker exec redis-replica-1 redis-cli -a myredispassword ping &> /dev/null; then
            print_success "Redis Replica 1: ACTIVO"
        else
            print_warning "Redis Replica 1: INACTIVO"
        fi

        # Test Redis Replica 2
        if docker exec redis-replica-2 redis-cli -a myredispassword ping &> /dev/null; then
            print_success "Redis Replica 2: ACTIVO"
        else
            print_warning "Redis Replica 2: INACTIVO"
        fi

        # Test Web
        if curl -s http://localhost:5000 > /dev/null 2>&1; then
            print_success "Aplicación Web: ACTIVO"
        else
            print_warning "Aplicación Web: INACTIVO"
        fi

        # Test Dashboard
        if curl -s http://localhost:8050 > /dev/null 2>&1; then
            print_success "Dashboard Métricas: ACTIVO"
        else
            print_warning "Dashboard Métricas: INACTIVO"
        fi

        # Test Cache Dashboard
        if curl -s http://localhost:5000/cache-dashboard > /dev/null 2>&1; then
            print_success "Dashboard Caché: ACTIVO"
        else
            print_warning "Dashboard Caché: INACTIVO"
        fi
        ;;

    4)
        print_header "======================================================="
        print_header "📜 LOGS EN TIEMPO REAL"
        print_header "======================================================="
        echo ""
        print_info "Mostrando logs (Ctrl+C para salir)..."
        echo ""
        docker-compose logs -f
        ;;

    5)
        print_header "======================================================="
        print_header "🛑 DETENIENDO SERVICIOS"
        print_header "======================================================="
        echo ""
        print_warning "Deteniendo todos los servicios..."
        docker-compose down
        print_success "✓ Servicios detenidos"
        ;;

    6)
        print_header "======================================================="
        print_header "🧹 LIMPIEZA Y REINICIO COMPLETO"
        print_header "======================================================="
        echo ""
        print_warning "Esta acción eliminará TODOS los datos (volúmenes, caché, etc.)"
        read -p "¿Estás seguro? (s/N): " confirm

        if [ "$confirm" = "s" ] || [ "$confirm" = "S" ]; then
            print_warning "Limpiando y reiniciando todo..."
            docker-compose down -v
            docker-compose up -d --build
            sleep 5
            print_success "✓ Sistema reiniciado desde cero"
        else
            print_info "Operación cancelada"
        fi
        ;;

    7)
        print_header "======================================================="
        print_header "🧪 PRUEBA DE CONECTIVIDAD COMPLETA"
        print_header "======================================================="
        echo ""

        # Test 1: Redis LOCAL
        print_info "Test 1: Redis LOCAL (eventos)"
        if docker exec redis-master redis-cli -a myredispassword SET test:connectivity "OK" &> /dev/null; then
            result=$(docker exec redis-master redis-cli -a myredispassword GET test:connectivity 2>/dev/null)
            if [ "$result" = "OK" ]; then
                print_success "Redis LOCAL: WRITE + READ OK"
            fi
        else
            print_error "Redis LOCAL: FALLO"
        fi

        # Test 2: Replicación
        print_info "Test 2: Replicación Redis"
        sleep 1
        if docker exec redis-replica-1 redis-cli -a myredispassword GET test:connectivity &> /dev/null; then
            print_success "Replicación: OK (dato replicado a replica-1)"
        else
            print_warning "Replicación: NO VERIFICABLE"
        fi

        # Test 3: API de productos
        print_info "Test 3: API de productos"
        if response=$(curl -s http://localhost:5000/api/products 2>/dev/null); then
            if echo "$response" | grep -q "data"; then
                print_success "API productos: OK"
            fi
        else
            print_warning "API productos: NO DISPONIBLE"
        fi

        # Test 4: API de caché stats
        print_info "Test 4: API de estadísticas de caché"
        if response=$(curl -s http://localhost:5000/api/cache/stats 2>/dev/null); then
            if echo "$response" | grep -q "cache_stats"; then
                print_success "API caché stats: OK"
            fi
        else
            print_warning "API caché stats: NO DISPONIBLE"
        fi

        echo ""
        print_success "✓ Tests de conectividad completados"
        ;;

    8)
        print_header "======================================================="
        print_header "⚡ TEST DE CACHÉ: MISS → HIT"
        print_header "======================================================="
        echo ""

        print_info "Este test demuestra el valor de Redis como caché"
        echo ""

        # Primera petición (esperamos MISS)
        print_highlight "Petición 1 (esperamos CACHE MISS):"
        response1=$(curl -s http://localhost:5000/api/products/1)
        echo "$response1" | jq '.' 2>/dev/null || echo "$response1"

        source=$(echo "$response1" | jq -r '.source' 2>/dev/null)
        latency1=$(echo "$response1" | jq -r '.latency_ms' 2>/dev/null)

        if [ "$source" = "database" ]; then
            print_success "✓ CACHE MISS (como esperado)"
            echo "   Latencia: ${latency1}ms (desde SQLite)"
        fi

        echo ""
        sleep 1

        # Segunda petición (esperamos HIT)
        print_highlight "Petición 2 (esperamos CACHE HIT):"
        response2=$(curl -s http://localhost:5000/api/products/1)
        echo "$response2" | jq '.' 2>/dev/null || echo "$response2"

        source2=$(echo "$response2" | jq -r '.source' 2>/dev/null)
        latency2=$(echo "$response2" | jq -r '.latency_ms' 2>/dev/null)

        if [ "$source2" = "cache" ]; then
            print_success "✓ CACHE HIT (desde Redis)"
            echo "   Latencia: ${latency2}ms"
        fi

        echo ""
        print_header "======================================================="
        print_highlight "📊 RESULTADO:"
        echo "   Latencia MISS:  ${latency1}ms (SQLite)"
        echo "   Latencia HIT:   ${latency2}ms (Redis)"
        if [ ! -z "$latency1" ] && [ ! -z "$latency2" ]; then
            improvement=$(echo "scale=1; ($latency1 - $latency2) / $latency1 * 100" | bc 2>/dev/null)
            echo "   Mejora:         ${improvement}% más rápido"
        fi
        print_header "======================================================="
        ;;

    9)
        print_header "======================================================="
        print_header "🔥 PRE-CALENTAR CACHÉ"
        print_header "======================================================="
        echo ""

        print_info "Enviando petición de warm-up..."
        response=$(curl -s -X POST http://localhost:5000/api/cache/warmup)
        echo "$response" | jq '.' 2>/dev/null || echo "$response"

        if echo "$response" | grep -q "success"; then
            print_success "✓ Caché pre-calentada con todos los productos"
        else
            print_error "Error pre-calentando caché"
        fi
        ;;

    10)
        print_header "======================================================="
        print_header "🎮 SIMULADOR DE TRÁFICO"
        print_header "======================================================="
        echo ""

        if [ ! -f "redis/WebApp/traffic_simulator.py" ]; then
            print_error "Archivo traffic_simulator.py no encontrado"
            exit 1
        fi

        print_info "El simulador generará usuarios virtuales con perfiles realistas"
        echo ""
        echo "Perfiles de usuario:"
        echo "  - Browser (40%):    Solo navega"
        echo "  - Researcher (25%): Investiga productos"
        echo "  - Buyer (15%):      Compra directamente"
        echo "  - Bouncer (20%):    Sale rápido"
        echo ""
        print_highlight "Abre estos dashboards en tu navegador:"
        echo "  - http://localhost:5000/cache-dashboard"
        echo "  - http://localhost:8050"
        echo ""
        read -p "Presiona ENTER para iniciar el simulador..."

        cd redis/WebApp

        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi

        source venv/bin/activate
        pip install -q -r requirements.txt

        print_success "Iniciando simulador (Ctrl+C para detener)..."
        echo ""
        python traffic_simulator.py
        ;;

    11)
        print_header "======================================================="
        print_header "🌐 URLs DE SERVICIOS"
        print_header "======================================================="
        echo ""
        echo "📱 APLICACIÓN WEB:"
        echo -e "   ${GREEN}http://localhost:5000${NC}"
        echo "   - Página principal de TechStore"
        echo ""
        echo "⚡ DASHBOARD DE CACHÉ (NUEVO):"
        echo -e "   ${GREEN}http://localhost:5000/cache-dashboard${NC}"
        echo "   - Hit rate, latencias, estadísticas"
        echo ""
        echo "📊 DASHBOARD DE MÉTRICAS:"
        echo -e "   ${GREEN}http://localhost:8050${NC}"
        echo "   - Gráfico de velas (candlestick)"
        echo ""
        echo "🔧 API ENDPOINTS:"
        echo -e "   ${CYAN}GET${NC}  http://localhost:5000/api/products"
        echo -e "   ${CYAN}GET${NC}  http://localhost:5000/api/products/1"
        echo -e "   ${CYAN}GET${NC}  http://localhost:5000/api/cache/stats"
        echo -e "   ${CYAN}POST${NC} http://localhost:5000/api/cache/warmup"
        echo -e "   ${CYAN}POST${NC} http://localhost:5000/api/cache/invalidate"
        echo ""
        echo "🔴 REDIS:"
        echo "   Master:    localhost:6379"
        echo "   Replica 1: localhost:6380"
        echo "   Replica 2: localhost:6381"
        echo "   Password:  myredispassword"
        echo ""
        ;;

    12)
        print_header "======================================================="
        print_header "📊 ESTADÍSTICAS DE CACHÉ"
        print_header "======================================================="
        echo ""

        response=$(curl -s http://localhost:5000/api/cache/stats)

        if echo "$response" | grep -q "cache_stats"; then
            echo "$response" | jq '.' 2>/dev/null || echo "$response"

            # Extraer valores
            hit_rate=$(echo "$response" | jq -r '.cache_stats.hit_rate' 2>/dev/null)
            hits=$(echo "$response" | jq -r '.cache_stats.hits' 2>/dev/null)
            misses=$(echo "$response" | jq -r '.cache_stats.misses' 2>/dev/null)
            total=$(echo "$response" | jq -r '.cache_stats.total_requests' 2>/dev/null)

            echo ""
            print_header "======================================================="
            print_highlight "RESUMEN:"
            echo "   Hit Rate:        ${hit_rate}%"
            echo "   Cache Hits:      ${hits}"
            echo "   Cache Misses:    ${misses}"
            echo "   Total Requests:  ${total}"
            print_header "======================================================="
        else
            print_error "No se pudieron obtener estadísticas"
        fi
        ;;

    13)
        print_header "======================================================="
        print_header "🔄 VERIFICACIÓN DE REPLICACIÓN REDIS"
        print_header "======================================================="
        echo ""

        print_info "Información de replicación del Master:"
        echo ""
        docker exec redis-master redis-cli -a myredispassword INFO replication 2>/dev/null | grep -E "role:|connected_slaves:"

        echo ""
        print_info "Información de Replica 1:"
        echo ""
        docker exec redis-replica-1 redis-cli -a myredispassword INFO replication 2>/dev/null | grep -E "role:|master_host:|master_link_status:"

        echo ""
        print_info "Información de Replica 2:"
        echo ""
        docker exec redis-replica-2 redis-cli -a myredispassword INFO replication 2>/dev/null | grep -E "role:|master_host:|master_link_status:"

        echo ""
        print_success "✓ Verificación completada"
        ;;

    14)
        print_header "======================================================="
        print_header "☁️ CONFIGURACIÓN DE REDIS CLOUD"
        print_header "======================================================="
        echo ""
        print_info "Guía rápida para configurar Redis Cloud:"
        echo ""
        echo "1. Crear cuenta en: https://redis.com/try-free/"
        echo "2. Crear base de datos FREE (30 MB gratis)"
        echo "3. Copiar credenciales:"
        echo "   - Host"
        echo "   - Port"
        echo "   - Password"
        echo ""
        echo "4. Configurar 4 ACLs (requisito práctica):"
        echo "   - admin_user"
        echo "   - cache_reader"
        echo "   - cache_writer"
        echo "   - metrics_user"
        echo ""
        echo "5. Actualizar docker-compose.yml con:"
        echo "   REDIS_CLOUD_HOST=tu-endpoint.cloud.redislabs.com"
        echo "   REDIS_CLOUD_PORT=12345"
        echo "   REDIS_CLOUD_PASSWORD=tu_password"
        echo ""
        print_highlight "📖 Guía completa: REDIS_CLOUD_SETUP.md"
        echo ""
        ;;

    15)
        print_info "Iniciando Redis localmente..."

        if pgrep redis-server > /dev/null; then
            print_warning "Redis ya está corriendo"
        else
            redis-server --daemonize yes --requirepass myredispassword
            print_success "Redis iniciado en puerto 6379"
        fi
        ;;

    16)
        print_info "Iniciando aplicación web (sin Docker)..."

        cd redis/WebApp

        # Verificar si existe venv
        if [ ! -d "venv" ]; then
            print_info "Creando entorno virtual..."
            python3 -m venv venv
        fi

        source venv/bin/activate

        # Instalar dependencias
        print_info "Instalando dependencias..."
        pip install -q -r requirements.txt

        # Iniciar aplicación
        print_success "Iniciando servidor Flask..."
        python app.py
        ;;

    0)
        print_info "Saliendo..."
        exit 0
        ;;

    *)
        print_error "Opción inválida"
        exit 1
        ;;
esac
