@echo off

if "%1"=="force" (
    docker compose -f compose.yml build --no-cache
)

docker compose -f compose.yml up --force-recreate