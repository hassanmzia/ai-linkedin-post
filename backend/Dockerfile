FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8052

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_data && gunicorn linkedin_agent.wsgi:application --bind 0.0.0.0:8052 --workers 4 --timeout 300"]
