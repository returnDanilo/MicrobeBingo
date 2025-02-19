FROM python:3.9-slim

ARG UNPRIV_UID_GID=444

WORKDIR /app
RUN chmod u=rwx,g=,o= /app
RUN chown $UNPRIV_UID_GID:$UNPRIV_UID_GID /app

USER $UNPRIV_UID_GID:$UNPRIV_UID_GID

COPY --chown=$UNPRIV_UID_GID:$UNPRIV_UID_GID . . 
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_CACHE_DIR=/app/uv_cache
RUN uv venv
RUN uv pip install --compile-bytecode --requirement requirements.txt

CMD ["uv", "run", "watchdog.py"]
