# Generic container image (Render, Fly, any Docker host). PORT is injected by the host.
FROM python:3.12-slim
RUN useradd -m -u 1000 user
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user . .
USER user
ENV PORT=7860 HOST=0.0.0.0 SCHEDULER=1 DB_PATH=/tmp/cypher.db
EXPOSE 7860
# One worker: the scheduler thread and SQLite lock live in this process.
CMD ["sh", "-c", "gunicorn app:app -b 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 180"]
