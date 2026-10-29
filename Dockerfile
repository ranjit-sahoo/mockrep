FROM python:3.11-slim
# eMudhra CA compromise (Oct 2026): keep the system CA store patched (Render advisory).
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
# eMudhra advisory: pip < 26.2.2 vendors a certifi bundle that still trusts the
# compromised emSign G3 root. Bootstrap pip from the hash-pinned wheel published
# in the official Python guidance (hash verified), then install requirements
# with the fixed pip. The #sha256 fragment makes the bootstrap download tamper-proof.
RUN pip install --no-cache-dir "pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV INTERVIEWPILOT_DB=/tmp/interviewpilot.sqlite3
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --proxy-headers --forwarded-allow-ips '*'"]
