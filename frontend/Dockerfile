# syntax=docker/dockerfile:1

# ---------- Stage 1: build ----------
FROM node:22-alpine AS build
WORKDIR /app

# Copy manifests first so `npm ci` stays cached until dependencies change
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build        # emits static files to /app/dist

# ---------- Stage 2: runtime ----------
FROM nginx:1.27-alpine AS runtime

# Drop the stock server block and use our own full config
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf

# Only the compiled static assets cross over from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Non-root: the nginx user ships with the image
USER nginx

# Unprivileged port (non-root cannot bind :80)
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
