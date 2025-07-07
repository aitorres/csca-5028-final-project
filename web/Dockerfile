FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN poetry install --no-root

CMD ["poetry", "run", "gunicorn", "-w", "2", "-b", "0.0.0:8080", "web.main:app"]
