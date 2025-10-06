FROM python:3.10-slim
WORKDIR /app
COPY services/pathway-pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/pathway-pipeline/ /app/
EXPOSE 8006
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8006"]

