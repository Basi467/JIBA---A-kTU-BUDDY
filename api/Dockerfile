# Pins the Python version — nothing in the repo did before this (evidenced
# by __pycache__ artifacts from both 3.11 and 3.13 on the dev machine).
FROM python:3.13-slim

WORKDIR /app

COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY src/ src/
COPY api/ api/
COPY database/ database/

# The live db path (KTU_DB_PATH, defaulting to database/ktu.db) is what the
# app reads/writes at runtime and is expected to be a mounted volume so data
# survives container restarts. This baked-in copy is only the seed used to
# populate that volume on its first run (see docker-entrypoint.sh) — it's
# never written to directly.
RUN mkdir -p /app/seed-data && cp database/ktu.db /app/seed-data/ktu.db
RUN chmod +x /app/api/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/api/docker-entrypoint.sh"]
