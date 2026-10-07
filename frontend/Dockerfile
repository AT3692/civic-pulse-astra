# syntax=docker/dockerfile:1

# ---------- Stage 1: build ----------
FROM node:22-alpine@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 AS build
WORKDIR /app

# Copy manifests first so `npm ci` stays cached until dependencies change
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build        # emits static files to /app/dist

# ---------- Stage 2: runtime ----------
FROM nginx:stable-alpine@sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94 AS runtime

# The pinned base predates these Alpine security fixes; keep the Trivy gate strict.
# CVE-2026-93990 (libexpat) and CVE-2026-103111 (pcre2).
RUN apk add --no-cache --upgrade libexpat=2.8.5-r0 pcre2=10.49-r0

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
