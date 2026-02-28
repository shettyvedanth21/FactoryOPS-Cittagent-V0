FROM python:3.11-slim

WORKDIR /app

COPY services/device-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/device-service/app/ ./app/
COPY services/device-service/start.sh ./start.sh
COPY services/device-service/alembic.ini ./alembic.ini
COPY shared/ ./shared/

RUN chmod +x start.sh

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["bash", "start.sh"]
