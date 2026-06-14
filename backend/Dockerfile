FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
COPY requirements-nlp.txt .
ARG INSTALL_LOCAL_NLP=false
RUN pip install --no-cache-dir -r requirements.txt
RUN if [ "$INSTALL_LOCAL_NLP" = "true" ]; then pip install --no-cache-dir -r requirements-nlp.txt; fi

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
