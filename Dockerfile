FROM python:3.11-slim
# eMudhra CA compromise (Oct 2026): keep the system CA store patched (Render advisory).
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV INTERVIEWPILOT_DB=/tmp/interviewpilot.sqlite3
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
