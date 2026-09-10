# --- Build stage ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
# Baked in at build time; override by rebuilding with a different --build-arg if the
# backend isn't reachable at this URL from wherever the browser loads the page.
ARG VITE_API_BASE_URL=http://localhost:8010/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# --- Serve stage ---
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
