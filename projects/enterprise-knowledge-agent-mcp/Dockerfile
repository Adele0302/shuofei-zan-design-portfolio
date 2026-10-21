FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd -m -u 10001 appuser
COPY . ./
RUN mkdir -p /app/local_data && chown -R appuser:appuser /app/local_data
USER appuser
EXPOSE 8000
CMD ["uvicorn","app.api:app","--host","0.0.0.0","--port","8000"]
