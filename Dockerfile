FROM python:3.12-slim

# Solo las 3 dependencias que necesita opencv-python-headless + mediapipe
# No se necesita display, GTK, GStreamer ni nada visual porque usamos la version headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Sustituimos opencv-python por la version headless antes de instalar.
# Headless no incluye GUI/display pero si VideoCapture y todo lo que necesitamos.
RUN sed 's/opencv-python==/opencv-python-headless==/g' requirements.txt > /tmp/requirements_docker.txt \
    && pip install --no-cache-dir -r /tmp/requirements_docker.txt

COPY . .

# Crear directorios necesarios en la imagen
RUN mkdir -p dataset modelo logs config

EXPOSE 5000

CMD ["python", "main.py"]
