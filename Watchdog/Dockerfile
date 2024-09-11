FROM python:3.9

WORKDIR /app

COPY . .

ARG UNPRIV_UID_GID=444

RUN chown -R $UNPRIV_UID_GID:$UNPRIV_UID_GID /app
RUN chmod -R u=r,g=,o= /app
RUN chmod u+x /app
RUN chmod u+x /app/watchdog.py

RUN pip install --no-cache-dir --requirement requirements.txt

USER $UNPRIV_UID_GID:$UNPRIV_UID_GID

CMD ["python", "watchdog.py"]
