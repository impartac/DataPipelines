# =============================================================================
# Data UI Dashboard - Docker Image
# =============================================================================
# Multi-stage: builder (would run npm build for React)
#              runtime: nginx serving static assets
# =============================================================================

# ---- Stage 1: builder (React/Node.js build step) ----
FROM node:20-alpine AS builder

LABEL stage=builder

WORKDIR /app

# In a real React project:
#   COPY package*.json ./
#   RUN npm ci --only=production
#   COPY src/ ./src/
#   COPY public/ ./public/
#   RUN npm run build
#
# For this demo we use pre-built static files:
COPY public/ ./build/

# ---- Stage 2: runtime ----
FROM nginx:1.25-alpine AS runtime

LABEL maintainer="hse-data-pipelines"
LABEL version="1.0.0"
LABEL description="Data Pipeline Dashboard UI"

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static assets from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
