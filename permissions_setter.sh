#!/bin/bash


if [ "$(id -u)" != "0" ] || [ -z "$SUDO_USER" ]; then
  echo "Script meant to be run as root! (and invoked with sudo) Exiting."
  exit 1
fi

echo '$SUDO_USER' is $SUDO_USER

cd "/home/$SUDO_USER/microbebingo"

umask 077

# Default to restric access for containers
chown -R $SUDO_USER:$SUDO_USER .
chmod -R u=rwX,g=,o= .

# Make sure files exist, otherwise docker will treat the paths as directories
touch last_heartbeat entered_channels.txt
mkdir -p logs public/cards

# Files the containers should have read access to
chmod -R o+rX public

# Files the containers should have read/write access to
chown -R :unpriv logs public/cards Caddy last_heartbeat entered_channels.txt
chmod -R g+rwX   logs public/cards Caddy last_heartbeat entered_channels.txt

# Make helpers executable
chmod u+x permissions_setter.sh docker-compose
