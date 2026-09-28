FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
COPY seed.py .
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

# Migrations run before the app starts; app binds to all interfaces inside the container.
# The entrypoint resolves SECRET_KEY first, since app.core.config refuses to
# initialise against Postgres while the key is still a placeholder.
# SEED_DEMO_DATA fills an empty database so a fresh `docker compose up` is
# immediately log-in-able; seed.py is idempotent, so it is a no-op afterwards.
ENTRYPOINT ["./entrypoint.sh"]
CMD ["sh", "-c", "alembic upgrade head && if [ \"$SEED_DEMO_DATA\" = \"true\" ]; then python seed.py; fi && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]