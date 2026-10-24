FROM node:22-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/src ./src
COPY frontend/public ./public
COPY backend/app/data /build/backend/app/data
RUN npm run build

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MATCHOS_ENV=production MATCHOS_AI_MODE=off MATCHOS_SPEECH_MODE=off
WORKDIR /app
COPY backend/pyproject.toml backend/constraints.txt ./backend/
COPY backend/app ./backend/app
RUN python -m pip install --no-cache-dir pip==26.2.1 setuptools==83.0.0 && python -m pip install --no-cache-dir -c backend/constraints.txt ./backend
COPY --from=frontend /build/frontend/dist ./frontend/dist
COPY deploy/start.py ./deploy/start.py
USER 10001:10001
EXPOSE 8000
CMD ["python", "deploy/start.py"]
