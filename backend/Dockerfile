FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install onchainos CLI — download Linux x86_64 binary directly from GitHub releases
RUN mkdir -p /root/.local/bin && \
    curl -fsSL -o /root/.local/bin/onchainos \
      https://github.com/okx/onchainos-skills/releases/download/v2.3.0/onchainos-x86_64-unknown-linux-gnu && \
    chmod +x /root/.local/bin/onchainos

# Add onchainos to PATH
ENV PATH="/root/.local/bin:${PATH}"

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
