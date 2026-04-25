FROM node:22-alpine

WORKDIR /app

# Copiar manifesto e instalar dependencias primero (mejor cache de Docker)
COPY package.json ./
RUN npm install

# Copiar el resto del codigo fuente
COPY . .

EXPOSE 5173

# Vite dev server con hot reload, escucha en todas las interfaces
CMD ["npm", "run", "dev"]
