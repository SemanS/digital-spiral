FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \ 
    && apt-get install -y --no-install-recommends curl \ 
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY mockjira ./mockjira
COPY clients ./clients
COPY examples ./examples
COPY scripts ./scripts
COPY requirements-contract.txt ./requirements-contract.txt

RUN pip install --no-cache-dir .

EXPOSE 9000

HEALTHCHECK CMD curl -f http://localhost:9000/docs || exit 1

CMD ["mock-jira-server", "--host", "0.0.0.0", "--port", "9000"]
