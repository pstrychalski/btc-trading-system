FROM python:3.10-slim

WORKDIR /app

COPY services/mesa-simulation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/mesa-simulation/ /app/

EXPOSE 8005

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8005"]

