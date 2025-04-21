#!/bin/bash

set -e

echo Copying files...
rsync --recursive --exclude .git -- "$(dirname $0)" myvm:"~/microbebingo" # Tip: You can use --delete to be more destructive 😈

echo Setting permissions...
ssh myvm "sudo ~/microbebingo/permissions_setter.sh"

echo Building, pulling and restarting containers if needed...
ssh myvm "cd microbebingo && ./docker-compose up --build --pull always -d && ./docker-compose restart caddy" # the Caddyfile file is not in an image, so changes to it won't be picked up by the build process

echo Cleaning up...
ssh myvm "docker system prune --force && docker image prune -a --force" # only prune dangling build cache, not all build cache

