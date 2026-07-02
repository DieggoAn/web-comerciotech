FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir pymongo fastapi uvicorn
COPY backend.py /app/
COPY templates/ /app/templates/
EXPOSE 8080
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8080"]
