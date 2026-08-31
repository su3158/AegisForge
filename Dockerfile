# syntax=docker/dockerfile:1

FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY . .

RUN if [ -f pyproject.toml ]; then uv sync --no-dev --extra postgres; fi

EXPOSE 8000

CMD ["uv", "run", "aegisforge", "serve", "--host", "0.0.0.0", "--port", "8000"]
