import time
from math import sin

from numpy.random import normal
import redis as rd



def connectDB(host: str = "localhost", port: int = 6379 , db: int  = 0) -> rd.Redis:
    """
    Conecta a una base de datos Redis en caso de existir conexión posible. En caso contrario devuelve None

    Args:
        host: Dirección IP en la que escucha la base de datos
        port: Puerto en el que escucha la base de datos
        db: Base de datos redis a la que conectarse
    """
    try:
        r = rd.Redis(host,port,db=db)
        r.ping()
        return r
    except rd.ConnectionError as e:
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
            r.expire(key, 30)  # Evitar sobreexceso de registros (30 segs)
            
            print(f"[{ts}] Peticiones generadas: {n_requests}")
            
            # Esperar hasta el siguiente segundo
            time.sleep(1)
    except KeyboardInterrupt:
        print("Simulación detenida")

if __name__ == "__main__":
    main()
