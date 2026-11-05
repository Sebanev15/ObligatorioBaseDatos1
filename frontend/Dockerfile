# --- Desarrollo: servidor de Vite con hot reload ---
FROM node:22-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]

# --- Build: genera la carpeta dist ---
FROM dev AS build
RUN npm run build

# --- Producción: nginx sirve los archivos ya compilados ---
FROM nginx:alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80