# Etapa 1: construir los archivos estaticos con Vite
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# Etapa 2: servir el build con Nginx
FROM nginx:alpine

# Instalar openssl para generar el certificado autofirmado
RUN apk add --no-cache openssl && \
    mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/handtalk.key \
      -out /etc/nginx/ssl/handtalk.crt \
      -subj "/C=GT/ST=Guatemala/O=USAC/CN=handtalk-ai"

# Copiar la configuracion de Nginx (proxy al backend + archivos estaticos)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar los archivos del build de Vite
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
