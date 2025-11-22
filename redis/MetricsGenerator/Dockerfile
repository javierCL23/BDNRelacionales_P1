FROM python:3.11-slim

WORKDIR /app

# Copiar archivos de configuración
COPY pyproject.toml .

# Instalar dependencias
RUN pip install --no-cache-dir redis dash plotly

# Copiar código
COPY . .

# Exponer puerto de Dash
EXPOSE 8050

ENV PYTHONUNBUFFERED=1

CMD ["python", "getCandles.py"]
