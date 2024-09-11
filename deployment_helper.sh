#!/bin/bash

set -e

echo Copying files...
# Tip: You can use --delete if you want to be more destructive 😈
rsync --recursive --exclude .git -- "$(dirname $0)" myvm:/home/dan/microbebingo

echo Setting permissions...
ssh myvm /home/dan/microbebingo/permissions_setter.sh

echo Restarting containers...
ssh myvm "bash -c 'cd microbebingo && ./docker-compose restart'"

echo
echo
echo Friendly reminder: Only restarted containers. Depending on your change, you might need to rebuild them too.
