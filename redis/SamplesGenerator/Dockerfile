FROM python:3.12-slim

WORKDIR /app

# Copiar archivos de configuración
COPY pyproject.toml .

# Instalar dependencias
RUN pip install --no-cache-dir redis numpy

# Copiar código
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "createSamples.py"]
