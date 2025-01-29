FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ARG UNPRIV_UID_GID=444

WORKDIR /app
RUN chmod u=rx,g=rx,o= /app
RUN chown $UNPRIV_UID_GID:$UNPRIV_UID_GID /app
COPY --chown=$UNPRIV_UID_GID:$UNPRIV_UID_GID . /app

RUN uv pip install --system --no-cache-dir --requirement requirements.txt

USER $UNPRIV_UID_GID:$UNPRIV_UID_GID

CMD ["python", "watchdog.py"]
