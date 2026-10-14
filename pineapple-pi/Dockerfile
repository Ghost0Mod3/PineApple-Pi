FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends iproute2 network-manager ca-certificates && rm -rf /var/lib/apt/lists/* && useradd -u 10001 -m pineapple
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
RUN mkdir -p database data logs && chown -R pineapple:pineapple /app
USER pineapple
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=3)" || exit 1
CMD ["uvicorn","backend.main:app","--host","0.0.0.0","--port","8000"]
