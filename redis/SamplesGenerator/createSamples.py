import time
import os
from math import sin

from numpy.random import normal
import redis as rd



def connectDB(host: str = None, port: int = None, db: int = 0, username: str = None, password: str = None) -> rd.Redis:
    """
    Conecta a una base de datos Redis CLOUD para métricas usando ACL.
    En caso de no existir conexión posible devuelve None

    Args:
        host: Dirección IP en la que escucha la base de datos
        port: Puerto en el que escucha la base de datos
        db: Base de datos redis a la que conectarse
        username: Usuario ACL de Redis (opcional)
        password: Contraseña de Redis (opcional)
    """
    # Usar variables de entorno de REDIS CLOUD si no se proporcionan
    if host is None:
        host = os.getenv('REDIS_CLOUD_HOST', None)
    if port is None:
        port = int(os.getenv('REDIS_CLOUD_PORT', 0))
    if username is None:
        username = os.getenv('REDIS_CLOUD_USER_WRITER', None)
    if password is None:
        password = os.getenv('REDIS_CLOUD_PASSWORD_WRITER', None)

    print(f"GETCANDLES: {host}:{port} | {username}:{password}")
    try:
        r = rd.Redis(
            host=host,
            port=port,
            db=db,
            username=username,
            password=password,
            decode_responses=False,
            socket_connect_timeout=10
        )
        r.ping()
        user_info = f" (usuario: {username})" if username else ""
        print(f"✓ Conectado a Redis CLOUD{user_info}: {host}:{port}")
        return r
    except rd.ConnectionError as e:
        print(f"✗ Error de conexión a Redis CLOUD: {e}")
        return None


def generateSamples(instant: int, media = 10, desv = 2, A = 5) -> int:
    """
    Genera el número de muestras aleatorias que se deben de mandar a la base de datos de Redis en base a un instante t.
    El algoritmo que usa se basa en una distribución con forma A*cos(t)+N(0,𝝈²)+µ con µ = media y 𝝈²=desv
    Para valores negativos redondea a 0 y en caso de decimales redondea a la unidad inferior más cercana
    """
    valor = max(A*sin(instant) + media + normal(media,desv,1),0)
    return round(valor[0])
    

def main():
    r = connectDB()
    if r is None:
        print("No se pudo conectar a Redis")
        return

    print("Iniciando simulación...")
    
    try:
        while True:
            # Tiempo actual en segundos
            ts = int(time.time())
            # Genera número de solicitudes para este segundo
            n_requests = generateSamples(ts)
            
            # Enviar a Redis número de solicitudes
            key = f"requests:{ts}"
            r.incrby(key, n_requests)
            r.expire(key, 120)  # Evitar sobreexceso de registros (120 segs) -> Suficientes para leer 20 velas
            
            print(f"[{ts}] Peticiones generadas: {n_requests}")
            
            # Esperar hasta el siguiente segundo
            time.sleep(1)
    except KeyboardInterrupt:
        print("Simulación detenida")

if __name__ == "__main__":
    main()
