# Monopoly Polymarket Agent System — metarunelabs.dev
FROM python:3.9
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /home
WORKDIR /home

RUN uv sync --frozen --no-dev
