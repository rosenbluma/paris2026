# Build frontend
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Production image
FROM python:3.12-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend
COPY --from=frontend /app/frontend/dist ./app/static

# Railway provides PORT env var
ENV PORT=8000
EXPOSE 8000

# Run the app (using shell form to expand $PORT)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
