"""
Generador de tráfico simulado para la aplicación web
Simula visitantes reales con comportamientos diversos
"""

import requests
import random
import time
import threading
from datetime import datetime
from faker import Faker

fake = Faker(['es_ES', 'en_US', 'fr_FR', 'de_DE'])

# Configuración
BASE_URL = "http://localhost:5000"
SIMULATION_DURATION = 3600  # 1 hora de simulación
MIN_USERS = 5
MAX_USERS = 25

# Listas de datos realistas
PRODUCTS = [
    {"id": "1", "name": "Smartphone Pro X"},
    {"id": "2", "name": "Laptop Ultra 15\""},
    {"id": "3", "name": "Auriculares Wireless"},
    {"id": "4", "name": "Smartwatch Fit"},
    {"id": "5", "name": "Cámara Digital 4K"},
    {"id": "6", "name": "Monitor Gaming 27\""},
    {"id": "7", "name": "Teclado Mecánico RGB"},
    {"id": "8", "name": "Ratón Gaming Pro"},
]

ARTICLES = [
    {"id": "1", "title": "Las nuevas tendencias en IA para 2025"},
    {"id": "2", "title": "Comparativa: Mejores smartphones del año"},
    {"id": "3", "title": "Cómo optimizar tu setup gaming"},
]

SEARCH_QUERIES = [
    "smartphone", "laptop", "auriculares", "gaming", "4k", "wireless",
    "mecánico", "rgb", "pro", "ultra", "ofertas", "descuentos"
]

REFERRERS = [
    "https://www.google.com/search?q=techstore",
    "https://www.facebook.com/",
    "https://twitter.com/",
    "https://www.instagram.com/",
    "direct",
    "https://www.reddit.com/r/technology",
    "https://news.ycombinator.com/",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


class VirtualUser:
    """
    Simula el comportamiento de un usuario real
    """

    def __init__(self, user_id):
        self.user_id = user_id
        self.session_id = f"sim_session_{user_id}_{int(time.time())}_{random.randint(1000, 9999)}"
        self.user_agent = random.choice(USER_AGENTS)
        self.referrer = random.choice(REFERRERS)
        self.ip_address = fake.ipv4()
        self.behavior_profile = self.generate_behavior_profile()

    def generate_behavior_profile(self):
        """
        Genera un perfil de comportamiento basado en tipos de usuario
        """
        profiles = {
            'browser': {  # Usuario que solo navega
                'page_views': random.randint(3, 8),
                'product_views': random.randint(2, 6),
                'add_to_cart_prob': 0.1,
                'search_prob': 0.3,
                'read_article_prob': 0.5,
                'session_duration': random.randint(60, 180)
            },
            'researcher': {  # Usuario que investiga antes de comprar
                'page_views': random.randint(8, 15),
                'product_views': random.randint(5, 12),
                'add_to_cart_prob': 0.3,
                'search_prob': 0.7,
                'read_article_prob': 0.8,
                'session_duration': random.randint(180, 600)
            },
            'buyer': {  # Usuario decidido a comprar
                'page_views': random.randint(2, 5),
                'product_views': random.randint(1, 3),
                'add_to_cart_prob': 0.8,
                'search_prob': 0.5,
                'read_article_prob': 0.2,
                'session_duration': random.randint(30, 120)
            },
            'bouncer': {  # Usuario que sale rápido
                'page_views': 1,
                'product_views': random.randint(0, 2),
                'add_to_cart_prob': 0.0,
                'search_prob': 0.1,
                'read_article_prob': 0.1,
                'session_duration': random.randint(5, 30)
            }
        }

        # Distribución realista de tipos de usuario
        profile_type = random.choices(
            list(profiles.keys()),
            weights=[40, 25, 15, 20],  # browser, researcher, buyer, bouncer
            k=1
        )[0]

        return profiles[profile_type]

    def send_event(self, event_type, event_data):
        """
        Envía un evento al servidor
        """
        try:
            event = {
                'session_id': self.session_id,
                'event_type': event_type,
                'timestamp': int(time.time() * 1000),
                'page_url': '/',
                'user_agent': self.user_agent,
                'referrer': self.referrer,
                'ip_address': self.ip_address,
                'screen_width': random.choice([1920, 1366, 1440, 375, 414]),
                'screen_height': random.choice([1080, 768, 900, 667, 896]),
                **event_data
            }

            response = requests.post(
                f"{BASE_URL}/api/track",
                json=event,
                timeout=5
            )

            if response.status_code == 200:
                return True
            else:
                print(f"Error {response.status_code}: {response.text}")
                return False

        except Exception as e:
            print(f"Error enviando evento: {e}")
            return False

    def simulate_session(self):
        """
        Simula una sesión completa de usuario
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Usuario {self.user_id} inició sesión")

        # Page view inicial
        self.send_event('page_view', {
            'referrer': self.referrer
        })

        time.sleep(random.uniform(1, 3))

        # Navegación por productos
        for _ in range(self.behavior_profile['product_views']):
            product = random.choice(PRODUCTS)
            self.send_event('product_view', {
                'product_id': product['id'],
                'product_name': product['name']
            })

            time.sleep(random.uniform(2, 8))

            # Decidir si añadir al carrito
            if random.random() < self.behavior_profile['add_to_cart_prob']:
                self.send_event('add_to_cart', {
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'price': f"{random.randint(50, 1500)}€"
                })
                time.sleep(random.uniform(1, 3))

        # Búsquedas
        if random.random() < self.behavior_profile['search_prob']:
            query = random.choice(SEARCH_QUERIES)
            self.send_event('search', {
                'query': query,
                'results_count': random.randint(0, 20)
            })
            time.sleep(random.uniform(2, 5))

        # Lectura de artículos
        if random.random() < self.behavior_profile['read_article_prob']:
            article = random.choice(ARTICLES)
            self.send_event('article_read', {
                'article_id': article['id'],
                'article_title': article['title']
            })
            time.sleep(random.uniform(5, 20))

        # Scroll depth
        self.send_event('scroll_depth', {
            'depth_percentage': random.randint(10, 100)
        })

        # Page exit
        session_time = random.randint(
            self.behavior_profile['session_duration'] // 2,
            self.behavior_profile['session_duration']
        )
        self.send_event('page_exit', {
            'total_time': session_time
        })

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Usuario {self.user_id} finalizó sesión ({session_time}s)")


class TrafficSimulator:
    """
    Coordina la simulación de múltiples usuarios
    """

    def __init__(self):
        self.active_threads = []
        self.user_counter = 0
        self.running = False

    def create_user(self):
        """
        Crea y ejecuta un nuevo usuario virtual
        """
        self.user_counter += 1
        user = VirtualUser(self.user_counter)

        thread = threading.Thread(target=user.simulate_session)
        thread.daemon = True
        thread.start()

        return thread

    def simulate_realistic_traffic(self, duration=SIMULATION_DURATION):
        """
        Simula tráfico realista con patrones temporales
        """
        self.running = True
        start_time = time.time()

        print("\n" + "="*60)
        print("🚀 SIMULADOR DE TRÁFICO WEB INICIADO")
        print("="*60)
        print(f"Duración: {duration}s")
        print(f"Usuarios concurrentes: {MIN_USERS}-{MAX_USERS}")
        print("="*60 + "\n")

        try:
            while self.running and (time.time() - start_time) < duration:
                # Limpiar threads terminados
                self.active_threads = [t for t in self.active_threads if t.is_alive()]

                # Calcular usuarios activos deseados basándose en hora del día
                current_hour = datetime.now().hour

                # Patrón de tráfico realista (más tráfico en horario laboral)
                if 9 <= current_hour < 12 or 14 <= current_hour < 18:
                    target_users = random.randint(MAX_USERS - 5, MAX_USERS)
                elif 18 <= current_hour < 22:
                    target_users = random.randint(MIN_USERS + 5, MAX_USERS - 2)
                else:
                    target_users = random.randint(MIN_USERS, MIN_USERS + 5)

                # Ajustar número de usuarios
                current_users = len(self.active_threads)

                if current_users < target_users:
                    # Crear nuevos usuarios
                    new_users = target_users - current_users
                    for _ in range(new_users):
                        thread = self.create_user()
                        self.active_threads.append(thread)

                # Esperar antes del siguiente ciclo
                time.sleep(random.uniform(3, 10))

        except KeyboardInterrupt:
            print("\n⚠️  Simulación interrumpida por el usuario")

        finally:
            self.running = False
            print("\n" + "="*60)
            print(f"✓ Simulación finalizada")
            print(f"✓ Total de usuarios simulados: {self.user_counter}")
            print("="*60 + "\n")


if __name__ == "__main__":
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print("✓ Servidor web detectado\n")
    except:
        print(f"✗ Error: No se puede conectar a {BASE_URL}")
        print("  Asegúrate de que la aplicación Flask esté corriendo\n")
        exit(1)

    # Iniciar simulación
    simulator = TrafficSimulator()
    simulator.simulate_realistic_traffic(duration=SIMULATION_DURATION)
