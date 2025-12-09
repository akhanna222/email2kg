# Multi-stage build for Email2KG Frontend

# Stage 1: Build the React application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with proper resolution
RUN npm install --legacy-peer-deps && \
    npm install ajv@^8.0.0 --legacy-peer-deps

# Copy source code
COPY . .

# Set API URL for production build
# Using HTTPS without port for cleaner URLs (nginx will proxy to backend:8000)
ENV REACT_APP_API_URL=https://agenticrag360.com/api

# Build the application
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose ports for HTTP and HTTPS
EXPOSE 80 443

# Health check (checks HTTP internally, HTTPS handled by nginx)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
