FROM python:3.11-slim

WORKDIR /app

COPY services/analytics-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/analytics-service/app/ ./app/
COPY services/analytics-service/start.sh ./start.sh
COPY services/analytics-service/alembic.ini ./alembic.ini
COPY services/analytics-service/alembic/ ./alembic/
COPY shared/ ./shared/

RUN chmod +x start.sh

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8003

CMD ["bash", "start.sh"]
