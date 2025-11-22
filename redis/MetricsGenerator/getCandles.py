import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import redis as rd
import time
import os
from datetime import datetime


def connectDB(host: str = None, port: int = None, db: int = 0, password: str = None) -> rd.Redis:
    """
    Conecta a una base de datos Redis en caso de existir conexión posible. En caso contrario devuelve None

    Args:
        host: Dirección IP en la que escucha la base de datos
        port: Puerto en el que escucha la base de datos
        db: Base de datos redis a la que conectarse
        password: Contraseña de Redis (opcional)
    """
    # Usar variables de entorno si no se proporcionan
    if host is None:
        host = os.getenv('REDIS_HOST', 'localhost')
    if port is None:
        port = int(os.getenv('REDIS_PORT', 6379))
    if password is None:
        password = os.getenv('REDIS_PASSWORD', None)

    try:
        r = rd.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
        r.ping()
        return r
    except rd.ConnectionError as e:
        print(f"Error de conexión: {e}")
        return None



# Conexión a Redis
r = connectDB()
if r is None:
    print("No se pudo conectar a Redis")
    exit()


# Aplicación web para métricas


interval = 5  # segundos por vela
max_candles = 20  # cuántas velas mostrar en pantalla

app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Número de Requests en tiempo real", style={'textAlign': 'center'}),
    dcc.Graph(id='candlestick-graph'),
    dcc.Interval(
        id='interval-component',
        interval=5000,  # actualización cada 5 segundos
        n_intervals=0
    )
])

def get_candles():
    """
    Lee los últimos max_candles*interval segundos de Redis
    y calcula velas tipo OHLC con ventanas no solapadas
    """
    ts_now = int(time.time())
    
    # Calcular el inicio alineado a intervalos de 5 segundos
    # Esto asegura que las ventanas siempre terminen en múltiplos de 5
    aligned_now = (ts_now // interval) * interval
    start_ts = aligned_now - (max_candles * interval)
    
    # Leer todos los valores del rango de tiempo
    all_counts = []
    for ts in range(start_ts, aligned_now + interval):
        val = r.get(f"requests:{ts}")
        count = int(val) if val is not None else 0
        all_counts.append((ts, count))
    
    # Agrupar en velas de `interval` segundos
    candles = []
    
    for i in range(max_candles):
        # Calcular el rango de tiempo para esta vela
        candle_start = start_ts + (i * interval)
        candle_end = candle_start + interval
        
        # Filtrar valores que pertenecen a esta vela [start, end)
        group = [(ts, val) for ts, val in all_counts 
                 if candle_start <= ts < candle_end]
        
        if not group:
            # Si no hay datos, crear vela con valores 0
            candles.append({
                'time': datetime.fromtimestamp(candle_end),
                'open': 0,
                'high': 0,
                'low': 0,
                'close': 0
            })
            continue
        
        # Calcular OHLC
        o = group[0][1]   # primer valor en la ventana
        c = group[-1][1]  # último valor en la ventana
        h = max(v for _, v in group)  # máximo
        l = min(v for _, v in group)  # mínimo
        
        candles.append({
            'time': datetime.fromtimestamp(candle_end),
            'open': o,
            'high': h,
            'low': l,
            'close': c
        })
    
    return candles

@app.callback(
    Output('candlestick-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    candles = get_candles()
    
    if not candles:
        return go.Figure()
    
    fig = go.Figure(go.Candlestick(
        x=[c['time'] for c in candles],
        open=[c['open'] for c in candles],
        high=[c['high'] for c in candles],
        low=[c['low'] for c in candles],
        close=[c['close'] for c in candles],
        increasing_line_color='green',
        decreasing_line_color='red',
        name='Requests'
    ))
    
    fig.update_layout(
        title=f'Flujo de visitas en la web (ventanas de {interval}s)',
        xaxis_title='Tiempo',
        yaxis_title='Número de Requests',
        xaxis_rangeslider_visible=False,
        height=600,
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Mejorar formato del eje X
    fig.update_xaxes(
        tickformat='%H:%M:%S',
        dtick=interval * 1000  # milliseconds
    )
    
    return fig

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)