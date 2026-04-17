FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y nodejs npm curl && rm -rf /var/lib/apt/lists/*

COPY . .

RUN curl -fsSL https://raw.githubusercontent.com/okx/onchainos/main/install.sh | bash || npm install -g @okx/onchainos-skills 2>/dev/null || true

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
