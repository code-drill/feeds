call app_build.cmd
docker compose -f compose.yml run --build --remove-orphans --rm -P feeds-site-builder /bin/bash