# Hugging Face Space (Docker). Pulls the public code from GitHub at build time, so you never upload code by hand.
# Update the app later: Space > Settings > "Factory rebuild".
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
ARG BRANCH=claude/wonderful-hopper-5jecz3
RUN git clone --depth 1 --branch ${BRANCH} https://github.com/rouvenwieland/cypher-news /app && chown -R user /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
USER user
# Open models (names verified on openrouter.ai/models on 2026-10-06). Change here if a model disappears.
ENV MODEL_PRIMARY=nvidia/nemotron-3-super-120b-a12b:free \
    MODEL_FALLBACK=nvidia/nemotron-3-ultra-550b-a55b:free \
    MODEL_VISION=google/gemma-4-31b-it:free \
    PORT=7860 HOST=0.0.0.0 SCHEDULER=1 DB_PATH=/tmp/cypher.db
EXPOSE 7860
CMD ["sh", "-c", "gunicorn app:app -b 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 180"]
