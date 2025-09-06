call app_build.cmd
docker compose -f compose.yml run --build --remove-orphans -P feeds-site-builder /bin/bash