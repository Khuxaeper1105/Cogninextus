FROM python:3.12-slim
WORKDIR /app
COPY app.py engine.py horizon.py reality.py operations.py sovereign.py production.py requirements-production.txt ./
COPY static ./static
RUN mkdir -p /app/data && chown -R 10001:10001 /app
USER 10001:10001
ENV HOST=0.0.0.0 PORT=8000 COGNI_DB=/app/data/cogni.sqlite PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000
CMD ["python", "app.py"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3).close()"]
