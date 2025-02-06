FROM python:3.9-slim

ARG UNPRIV_UID_GID=444

WORKDIR /app
RUN chmod u=rwx,g=,o= /app
RUN chown $UNPRIV_UID_GID:$UNPRIV_UID_GID /app

USER $UNPRIV_UID_GID:$UNPRIV_UID_GID

COPY --chown=$UNPRIV_UID_GID:$UNPRIV_UID_GID . . 
# Setting HOME is needed for pip to install for --user successfully. 
ENV HOME /app
RUN pip install --user --no-cache-dir --requirement requirements.txt

CMD ["python", "watchdog.py"]
