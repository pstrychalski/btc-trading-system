FROM python:3.10-slim
WORKDIR /app
COPY services/rl-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/rl-agent/ /app/
EXPOSE 8007
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8007"]

