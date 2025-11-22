"""
Capa de caché usando Redis Cloud
Implementa el patrón Cache-Aside (Lazy Loading)
Esta capa NO interfiere con el histórico de Cassandra
"""

import redis
import json
import time
from typing import Optional, Any, Dict
from datetime import datetime


class RedisCache:
    """
    Implementación de Redis como caché de lectura
    Patrón: Cache-Aside (también llamado Lazy Loading)

    Flujo:
    1. Aplicación consulta caché
    2. Si existe (HIT) → retorna inmediatamente
    3. Si no existe (MISS) → consulta BD tradicional
    4. Guarda en caché para próximas consultas
    5. Retorna al usuario

    IMPORTANTE: Esta caché es VOLÁTIL y TEMPORAL
    - NO es la fuente de verdad (source of truth = SQLite)
    - Cassandra se alimentará de SQLite, NO de esta caché
    """

    def __init__(self, host: str, port: int, password: Optional[str] = None, db: int = 0):
        """
        Inicializar conexión a Redis Cloud (o local si Cloud no está configurado)
        """
        try:
            self.redis = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Verificar conexión
            self.redis.ping()
            self.connected = True
            print(f"✓ Caché conectada a Redis en {host}:{port}")
        except Exception as e:
            print(f"✗ Error conectando a Redis caché: {e}")
            print("  → La app funcionará sin caché (todas las consultas irán a BD)")
            self.connected = False
            self.redis = None

        # Configuración de TTLs (Time To Live) por tipo de dato
        self.TTL_PRODUCT = 1800       # 30 minutos - productos cambian poco
        self.TTL_PRODUCT_LIST = 600   # 10 minutos - lista completa
        self.TTL_USER = 900           # 15 minutos - datos de usuario
        self.TTL_CONFIG = 3600        # 1 hora - configuración global
        self.TTL_CATEGORY = 1200      # 20 minutos - productos por categoría

        # Prefijos para organizar las claves en Redis
        self.PREFIX_PRODUCT = "cache:product:"
        self.PREFIX_PRODUCTS_ALL = "cache:products:all"
        self.PREFIX_CATEGORY = "cache:category:"
        self.PREFIX_USER = "cache:user:"
        self.PREFIX_CONFIG = "cache:config:"

    def _is_available(self) -> bool:
        """Verificar si la caché está disponible"""
        return self.connected and self.redis is not None

    # ==================== OPERACIONES BÁSICAS ====================

    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor de caché
        Retorna None si no existe o si hay error
        """
        if not self._is_available():
            return None

        try:
            value = self.redis.get(key)
            if value:
                # Incrementar contador de hits
                self.redis.incr('cache:stats:hits')
                return json.loads(value)
            else:
                # Incrementar contador de misses
                self.redis.incr('cache:stats:misses')
                return None
        except Exception as e:
            print(f"Error leyendo de caché (key={key}): {e}")
            self.redis.incr('cache:stats:errors')
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Guardar valor en caché con TTL
        Retorna True si se guardó correctamente
        """
        if not self._is_available():
            return False

        try:
            serialized = json.dumps(value, default=str)  # default=str para fechas
            self.redis.setex(
                key,
                ttl or self.TTL_PRODUCT,
                serialized
            )
            return True
        except Exception as e:
            print(f"Error escribiendo en caché (key={key}): {e}")
            self.redis.incr('cache:stats:errors')
            return False

    def delete(self, key: str):
        """
        Invalidar caché (eliminar una clave)
        Útil cuando se actualiza un producto en la BD
        """
        if not self._is_available():
            return False

        try:
            self.redis.delete(key)
            self.redis.incr('cache:stats:invalidations')
            return True
        except Exception as e:
            print(f"Error eliminando de caché (key={key}): {e}")
            return False

    def delete_pattern(self, pattern: str):
        """
        Invalidar múltiples claves por patrón
        Ejemplo: delete_pattern("cache:product:*") elimina todos los productos
        """
        if not self._is_available():
            return False

        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                self.redis.incrby('cache:stats:invalidations', len(keys))
            return True
        except Exception as e:
            print(f"Error eliminando patrón de caché (pattern={pattern}): {e}")
            return False

    # ==================== PRODUCTOS ====================

    def get_product(self, product_id: int) -> Optional[Dict]:
        """Obtener un producto específico de caché"""
        key = f"{self.PREFIX_PRODUCT}{product_id}"
        return self.get(key)

    def set_product(self, product_id: int, product_data: Dict):
        """Guardar un producto en caché"""
        key = f"{self.PREFIX_PRODUCT}{product_id}"
        return self.set(key, product_data, ttl=self.TTL_PRODUCT)

    def invalidate_product(self, product_id: int):
        """Invalidar caché de un producto (cuando se actualiza)"""
        key = f"{self.PREFIX_PRODUCT}{product_id}"
        return self.delete(key)

    def get_all_products(self) -> Optional[list]:
        """Obtener lista completa de productos de caché"""
        return self.get(self.PREFIX_PRODUCTS_ALL)

    def set_all_products(self, products: list):
        """Guardar lista completa de productos en caché"""
        return self.set(self.PREFIX_PRODUCTS_ALL, products, ttl=self.TTL_PRODUCT_LIST)

    def invalidate_all_products(self):
        """Invalidar lista de productos (cuando se añade/elimina uno)"""
        return self.delete(self.PREFIX_PRODUCTS_ALL)

    def get_products_by_category(self, category: str) -> Optional[list]:
        """Obtener productos por categoría de caché"""
        key = f"{self.PREFIX_CATEGORY}{category}"
        return self.get(key)

    def set_products_by_category(self, category: str, products: list):
        """Guardar productos por categoría en caché"""
        key = f"{self.PREFIX_CATEGORY}{category}"
        return self.set(key, products, ttl=self.TTL_CATEGORY)

    # ==================== USUARIOS ====================

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Obtener datos de usuario de caché"""
        key = f"{self.PREFIX_USER}{user_id}"
        return self.get(key)

    def set_user(self, user_id: int, user_data: Dict):
        """Guardar datos de usuario en caché"""
        key = f"{self.PREFIX_USER}{user_id}"
        return self.set(key, user_data, ttl=self.TTL_USER)

    def invalidate_user(self, user_id: int):
        """Invalidar caché de usuario (cuando actualiza perfil)"""
        key = f"{self.PREFIX_USER}{user_id}"
        return self.delete(key)

    # ==================== CONFIGURACIÓN ====================

    def get_config(self, config_key: str) -> Optional[str]:
        """Obtener valor de configuración de caché"""
        key = f"{self.PREFIX_CONFIG}{config_key}"
        result = self.get(key)
        return result['value'] if result else None

    def set_config(self, config_key: str, value: str):
        """Guardar configuración en caché"""
        key = f"{self.PREFIX_CONFIG}{config_key}"
        return self.set(key, {'value': value}, ttl=self.TTL_CONFIG)

    def get_all_config(self) -> Optional[Dict]:
        """Obtener toda la configuración de caché"""
        key = f"{self.PREFIX_CONFIG}all"
        return self.get(key)

    def set_all_config(self, config_dict: Dict):
        """Guardar toda la configuración en caché"""
        key = f"{self.PREFIX_CONFIG}all"
        return self.set(key, config_dict, ttl=self.TTL_CONFIG)

    # ==================== ESTADÍSTICAS ====================

    def get_stats(self) -> Dict:
        """
        Obtener estadísticas de eficiencia de la caché
        Esto es MUY útil para la presentación: mostrar el valor de Redis
        """
        if not self._is_available():
            return {
                'status': 'disconnected',
                'hits': 0,
                'misses': 0,
                'errors': 0,
                'invalidations': 0,
                'total_requests': 0,
                'hit_rate': 0
            }

        try:
            hits = int(self.redis.get('cache:stats:hits') or 0)
            misses = int(self.redis.get('cache:stats:misses') or 0)
            errors = int(self.redis.get('cache:stats:errors') or 0)
            invalidations = int(self.redis.get('cache:stats:invalidations') or 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0

            return {
                'status': 'connected',
                'hits': hits,
                'misses': misses,
                'errors': errors,
                'invalidations': invalidations,
                'total_requests': total,
                'hit_rate': round(hit_rate, 2)
            }
        except Exception as e:
            print(f"Error obteniendo stats de caché: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }

    def reset_stats(self):
        """Resetear estadísticas (útil para demos)"""
        if not self._is_available():
            return False

        try:
            self.redis.delete(
                'cache:stats:hits',
                'cache:stats:misses',
                'cache:stats:errors',
                'cache:stats:invalidations'
            )
            return True
        except Exception as e:
            print(f"Error reseteando stats: {e}")
            return False

    def get_info(self) -> Dict:
        """
        Obtener información general de Redis (para observabilidad)
        """
        if not self._is_available():
            return {'status': 'disconnected'}

        try:
            info = self.redis.info()
            return {
                'status': 'connected',
                'version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec'),
                'keyspace': info.get('db0', {})
            }
        except Exception as e:
            print(f"Error obteniendo info de Redis: {e}")
            return {'status': 'error', 'error_message': str(e)}

    # ==================== UTILIDADES ====================

    def flush_all(self):
        """
        PELIGRO: Eliminar TODA la caché
        Usar solo en desarrollo/testing
        """
        if not self._is_available():
            return False

        try:
            self.redis.flushdb()
            print("⚠️  Caché completamente eliminada")
            return True
        except Exception as e:
            print(f"Error eliminando toda la caché: {e}")
            return False

    def warm_up(self, products: list):
        """
        Pre-calentar la caché con productos populares
        Útil para ejecutar antes de una demo o después de despliegue
        """
        if not self._is_available():
            return False

        try:
            # Guardar lista completa
            self.set_all_products(products)

            # Guardar cada producto individualmente
            for product in products:
                self.set_product(product['id'], product)

            # Agrupar por categoría
            by_category = {}
            for product in products:
                cat = product.get('category', 'Other')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(product)

            # Guardar por categoría
            for category, prods in by_category.items():
                self.set_products_by_category(category, prods)

            print(f"✓ Caché pre-calentada con {len(products)} productos")
            return True
        except Exception as e:
            print(f"Error pre-calentando caché: {e}")
            return False
