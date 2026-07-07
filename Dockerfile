FROM python:3.11-slim
WORKDIR /app

# 🔒 Versiones fijadas para mitigar cambios destructivos en el futuro
RUN pip install --no-cache-dir \
    pymongo==4.8.0 \
    fastapi==0.115.0 \
    "starlette>=0.37,<0.38" \
    uvicorn==0.30.6 \
    jinja2==3.1.4 \
    python-multipart==0.0.9 \
    mysql-connector-python==8.0.33

COPY backend.py /app/
COPY templates/ /app/templates/
EXPOSE 8080
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8080"]