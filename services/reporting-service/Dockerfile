FROM python:3.11-slim

WORKDIR /app

COPY services/reporting-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/reporting-service/app/ ./app/
COPY services/reporting-service/start.sh ./start.sh
COPY services/reporting-service/alembic.ini ./alembic.ini
COPY shared/ ./shared/

RUN chmod +x start.sh

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["bash", "start.sh"]
