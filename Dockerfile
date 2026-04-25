FROM python:3.12-slim

# Dependencias del sistema que necesita OpenCV para correr sin display
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorios necesarios en la imagen
RUN mkdir -p dataset modelo logs config

EXPOSE 5000

CMD ["python", "main.py"]
