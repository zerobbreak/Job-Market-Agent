# Build stage
FROM node:20-alpine AS build-env
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies with optimizations
# - Skip scripts (prepare, postinstall, etc.)
# - Use cache mount for npm cache to speed up rebuilds
# - Production only would be --omit=dev but we need dev deps for build
RUN --mount=type=cache,target=/root/.npm \
    npm ci --ignore-scripts --prefer-offline

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage - serve SPA with nginx
FROM nginx:stable-alpine

# Install gettext for envsubst
RUN apk add --no-cache gettext

# Copy built application from build stage
COPY --from=build-env /app/build/client /usr/share/nginx/html

# Copy custom nginx configuration for SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose port 80
EXPOSE 80

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Use custom entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
