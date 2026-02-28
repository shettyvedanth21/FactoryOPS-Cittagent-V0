FROM python:3.11-slim

WORKDIR /app

COPY services/data-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/data-service/src/ ./src/
COPY shared/ ./shared/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8081"]
