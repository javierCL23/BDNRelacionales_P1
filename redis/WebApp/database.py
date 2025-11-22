"""
Base de datos tradicional (SQLite) - Source of Truth
Esta es la base de datos principal, Redis y Cassandra son capas encima
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    """
    Base de datos tradicional usando SQLite
    Almacena el estado definitivo (source of truth)
    Redis actúa como caché delante de esta BD
    Cassandra almacena el histórico de eventos
    """

    def __init__(self, db_path='techstore.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Crear tablas si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price REAL,
                category TEXT,
                stock INTEGER,
                image_url TEXT,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de usuarios (para futuras funcionalidades)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de configuración global
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        # Seed inicial
        self.seed_products()
        self.seed_config()

    def seed_products(self):
        """Insertar productos de ejemplo si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verificar si ya hay productos
        cursor.execute('SELECT COUNT(*) FROM products')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        products = [
            (1, 'Smartphone Pro X', '5G, 256GB, Cámara 108MP', 899.99, 'Smartphones', 50, '/static/img/phone.jpg'),
            (2, 'Laptop Ultra 15"', 'Intel i7, 16GB RAM, 512GB SSD', 1299.99, 'Laptops', 30, '/static/img/laptop.jpg'),
            (3, 'Auriculares BT Pro', 'Cancelación de ruido activa, 30h batería', 249.99, 'Audio', 100, '/static/img/headphones.jpg'),
            (4, 'Smartwatch Fit', 'Monitor cardíaco, GPS, Resistente al agua', 199.99, 'Wearables', 75, '/static/img/watch.jpg'),
            (5, 'Tablet Pro 12"', 'Apple M1, 128GB, Pencil compatible', 799.99, 'Tablets', 40, '/static/img/tablet.jpg'),
            (6, 'Cámara 4K Pro', 'Sensor 24MP, Grabación 4K 60fps', 1499.99, 'Cámaras', 20, '/static/img/camera.jpg'),
            (7, 'Altavoz Smart', 'Alexa integrada, Sonido 360°', 149.99, 'Audio', 120, '/static/img/speaker.jpg'),
            (8, 'Consola Next-Gen', 'Ray tracing, 1TB SSD, 4K 120fps', 499.99, 'Gaming', 60, '/static/img/console.jpg'),
        ]

        cursor.executemany(
            'INSERT INTO products (id, name, description, price, category, stock, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)',
            products
        )

        conn.commit()
        conn.close()
        print("✓ Productos insertados en la base de datos")

    def seed_config(self):
        """Insertar configuración inicial"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        config_items = [
            ('site_name', 'TechStore'),
            ('maintenance_mode', 'false'),
            ('featured_category', 'Smartphones'),
            ('discount_active', 'false')
        ]

        for key, value in config_items:
            cursor.execute(
                'INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)',
                (key, value)
            )

        conn.commit()
        conn.close()

    # ==================== PRODUCTOS ====================

    def get_product(self, product_id: int) -> Optional[Dict]:
        """
        Obtener un producto por ID
        Nota: Esta función será llamada SOLO en caso de cache miss
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_products(self) -> List[Dict]:
        """
        Obtener todos los productos
        Nota: Esta función será llamada SOLO en caso de cache miss
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM products ORDER BY id')
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Obtener productos por categoría"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM products WHERE category = ? ORDER BY name', (category,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_product_views(self, product_id: int):
        """Incrementar contador de visualizaciones de un producto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE products SET views = views + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (product_id,)
        )

        conn.commit()
        conn.close()

    def update_product_stock(self, product_id: int, quantity: int):
        """Actualizar stock de un producto (para futuras compras)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE products SET stock = stock - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (quantity, product_id)
        )

        conn.commit()
        conn.close()

    # ==================== USUARIOS ====================

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Obtener un usuario por ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            user = dict(row)
            # Parsear JSON de preferencias si existe
            if user.get('preferences'):
                user['preferences'] = json.loads(user['preferences'])
            return user
        return None

    def create_user(self, username: str, email: str, preferences: Dict = None) -> int:
        """Crear un nuevo usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO users (username, email, preferences) VALUES (?, ?, ?)',
            (username, email, json.dumps(preferences) if preferences else None)
        )

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return user_id

    # ==================== CONFIGURACIÓN ====================

    def get_config(self, key: str) -> Optional[str]:
        """Obtener valor de configuración"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None

    def set_config(self, key: str, value: str):
        """Establecer valor de configuración"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            (key, value)
        )

        conn.commit()
        conn.close()

    def get_all_config(self) -> Dict[str, str]:
        """Obtener toda la configuración"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT key, value FROM config')
        rows = cursor.fetchall()
        conn.close()

        return {row['key']: row['value'] for row in rows}

    # ==================== ESTADÍSTICAS ====================

    def get_stats(self) -> Dict:
        """Obtener estadísticas generales de la BD"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total de productos
        cursor.execute('SELECT COUNT(*) FROM products')
        total_products = cursor.fetchone()[0]

        # Total de usuarios
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        # Productos más vistos
        cursor.execute('SELECT id, name, views FROM products ORDER BY views DESC LIMIT 5')
        top_products = [{'id': row[0], 'name': row[1], 'views': row[2]} for row in cursor.fetchall()]

        conn.close()

        return {
            'total_products': total_products,
            'total_users': total_users,
            'top_products': top_products
        }

    # ==================== HISTÓRICO PARA CASSANDRA ====================

    def get_products_for_cassandra_seed(self) -> List[Dict]:
        """
        Obtener productos en formato listo para insertar en Cassandra
        Esta función será usada en la Parte B para el seeding inicial
        """
        products = self.get_all_products()

        # Convertir a formato compatible con Cassandra
        cassandra_products = []
        for p in products:
            cassandra_products.append({
                'product_id': p['id'],
                'product_name': p['name'],
                'category': p['category'],
                'price': p['price'],
                'stock': p['stock'],
                'created_at': p.get('created_at', datetime.now().isoformat())
            })

        return cassandra_products
