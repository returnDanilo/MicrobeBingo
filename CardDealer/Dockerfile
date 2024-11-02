FROM python:3.9-slim

ARG UNPRIV_UID_GID=444

WORKDIR /app
RUN chmod u=rx,g=,o= /app
RUN chown $UNPRIV_UID_GID:$UNPRIV_UID_GID /app

RUN apt update && apt install ffmpeg -y

COPY --chown=$UNPRIV_UID_GID:$UNPRIV_UID_GID requirements.txt requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt

COPY --chown=$UNPRIV_UID_GID:$UNPRIV_UID_GID . . 

USER $UNPRIV_UID_GID:$UNPRIV_UID_GID

CMD ["python", "carddealer.py"]
