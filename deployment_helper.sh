#!/bin/bash

set -e

echo Copying files...
rsync --recursive --exclude .git -- "$(dirname $0)" myvm:"~/microbebingo" # Tip: You can use --delete to be more destructive 😈

echo Setting permissions...
ssh myvm "~/microbebingo/permissions_setter.sh"

echo Building and restarting containers if needed...
ssh myvm "cd microbebingo && ./docker-compose up -d --build && ./docker-compose restart caddy" # Caddyfile is not in an image so changes won't be picked up by the build process

