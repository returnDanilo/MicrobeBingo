#!/bin/bash

if [ "$(id -u)" -eq 0 ]; then
  echo "This script should not be run as root! It's intended to be run as a user with sudo powers. Exiting."
  exit 1
fi

# Everything else should be disallowed for containers
sudo chown -R $USER:$USER ~/microbebingo
sudo chmod -R u=rwX,g=,o= ~/microbebingo

cd ~/microbebingo

# Create things if they don't exist
sudo touch last_heartbeat entered_channels
sudo mkdir -p logs public/cards

# Files the containers should only have read access to
sudo chmod -R o+rX public

# Files the containers will have read/write access to
sudo chown -R :unpriv logs public/cards Caddy last_heartbeat entered_channels
sudo chmod -R g+rwX   logs public/cards Caddy last_heartbeat entered_channels

# Helper executables
sudo chmod u+x permissions_setter.sh docker-compose
