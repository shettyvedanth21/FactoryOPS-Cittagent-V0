FROM python:3.11-slim

WORKDIR /app

COPY services/data-export-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/data-export-service/app/ ./app/
COPY services/data-export-service/start.sh ./start.sh
COPY services/data-export-service/alembic.ini ./alembic.ini
COPY services/data-export-service/alembic/ ./alembic/
COPY shared/ ./shared/

RUN chmod +x start.sh

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["bash", "start.sh"]
