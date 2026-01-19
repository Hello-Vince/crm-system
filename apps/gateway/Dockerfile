# syntax=docker/dockerfile:1.5
# Stage 1: Builder
FROM node:24.13.0-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Runtime
FROM node:24.13.0-alpine AS runtime

WORKDIR /app
ENV NODE_ENV=production

# Copy only production dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Copy built assets
COPY --from=builder /app/dist ./dist

# Non-root user (node user exists in official image)
USER node

EXPOSE 4000
CMD ["node", "dist/index.js"]
