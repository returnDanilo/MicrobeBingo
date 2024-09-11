#!/bin/bash

if [ "$(id -u)" -eq 0 ]; then
  echo "Error. This script should not be run as root. It's intended to be run as a user in the sudoers file. Exiting."
  exit 1
fi

cd ~/microbebingo

mkdir -p logs
mkdir -p public/cards

sudo chown -R $USER:$USER ~
sudo chmod -R u=rw,g=,o= ~
sudo chmod -R u+X ~

sudo chmod u+x        deployment_helper.sh
sudo chmod u+x        permissions_setter.sh
sudo chmod u+x        docker-compose

sudo chown -R :unpriv logs
sudo chmod -R g+rwX   logs

sudo chmod -R o+rX    public
sudo chown -R :unpriv public/cards
sudo chmod -R g+rwX   public/cards

sudo chown -R :unpriv Caddy
sudo chmod -R g+rwX   Caddy

sudo touch            last_heartbeat
sudo chown :unpriv    last_heartbeat
sudo chmod g+rw       last_heartbeat

sudo touch            entered_channels.txt
sudo chown :unpriv    entered_channels.txt
sudo chmod g+rw       entered_channels.txt
