# Deployment Guide

This project can be deployed as a Docker Compose app on a VPS, or split across managed services such as Render/Railway.

## Production Checklist

- Rotate any API keys that were printed in terminal logs.
- Set a strong `JWT_SECRET_KEY`.
- Set a strong `POSTGRES_PASSWORD`.
- Use PostgreSQL, not SQLite.
- Set `ENV=production`.
- Set `FRONTEND_ORIGINS` to the real frontend URL list.
- Set `NEXT_PUBLIC_API_URL` to the public backend URL before building the frontend.
- Do not expose PostgreSQL to the public internet.
- Run backend migrations.
- Confirm `/health` returns `{"status":"ok"}`.
- Add screenshots to `docs/screenshots/` before publishing the portfolio repository.

## Required Environment Variables

Backend:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
ENV=production
FRONTEND_ORIGIN=https://your-frontend-domain.com
FRONTEND_ORIGINS=["https://your-frontend-domain.com"]
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MAX_UPLOAD_BYTES=5242880
MAX_PDF_PAGES=30
AUTH_RATE_LIMIT=10
AUTH_RATE_WINDOW_SECONDS=60
ANALYSIS_RATE_LIMIT=20
ANALYSIS_RATE_WINDOW_SECONDS=3600
GENERATION_RATE_LIMIT=30
GENERATION_RATE_WINDOW_SECONDS=3600
```

Frontend build:

```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

## VPS With Docker Compose

1. Install Docker and Docker Compose plugin.
2. Copy the project to the server.
3. Set environment variables in the shell or in a secure `.env` file managed outside Git.
4. Build and start:

```bash
export GROQ_API_KEY="your_key"
export LLM_PROVIDER="groq"
export JWT_SECRET_KEY="replace-with-a-long-random-secret"
export POSTGRES_PASSWORD="replace-with-a-long-random-db-password"
export ENV="production"
export FRONTEND_ORIGINS='["https://your-frontend-domain.com"]'
export NEXT_PUBLIC_API_URL="https://your-backend-domain.com"
docker compose up --build -d
```

5. Check logs:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

6. Check health:

```bash
curl http://localhost:8000/health
```

For public HTTPS, put Nginx or Caddy in front of the app.

## Render/Railway Split Deploy

Recommended split:

- PostgreSQL: managed database
- Backend: FastAPI service
- Frontend: Next.js service

Backend start command:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Frontend build command:

```bash
npm ci && npm run build
```

Frontend start command:

```bash
npm run start
```

Set `NEXT_PUBLIC_API_URL` before frontend build, because Next.js embeds it into the client bundle.

## Smoke Test After Deploy

1. Open frontend URL.
2. Register a test user.
3. Upload a small PDF/TXT resume.
4. Run `NLP Local`.
5. Run `Groq Llama` if `GROQ_API_KEY` is configured.
6. Generate cover letter.
7. Export PDF report.
8. Refresh page and confirm history persists.
