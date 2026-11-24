FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 COGNI_SECURE_COOKIE=1 COGNI_DB=/tmp/cogninexus/cogni.sqlite
COPY CogniNexus-V4-Render-Free.zip /tmp/cogninexus-release.zip
RUN python -m zipfile -e /tmp/cogninexus-release.zip /app \
    && rm /tmp/cogninexus-release.zip \
    && pip install --no-cache-dir -r requirements-production.txt \
    && python -m unittest discover -s tests -q \
    && mkdir -p /app/data /tmp/cogninexus \
    && chown -R 10001:10001 /app/data /tmp/cogninexus
USER 10001:10001
EXPOSE 8000
CMD ["python", "production.py"]
