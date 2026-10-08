FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorio de subida de archivos si no existe
RUN mkdir -p /app/uploads/anexos /app/uploads/respuestas

EXPOSE 8000

# WATCHFILES_FORCE_POLLING: los bind mounts de Docker sobre Windows no emiten
# eventos inotify dentro del contenedor Linux; el watcher nativo falla con
# "Bad address" y el backend queda sirviendo codigo obsoleto. Con polling,
# watchfiles sondea el sistema de archivos y los cambios se detectan siempre.
ENV WATCHFILES_FORCE_POLLING=true
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
