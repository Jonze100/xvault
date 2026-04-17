FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install onchainos CLI
RUN curl -fsSL https://raw.githubusercontent.com/nicefellow1234/onchainos-skills/main/install.sh | bash || true

# Add onchainos to PATH
ENV PATH="/root/.local/bin:${PATH}"

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
