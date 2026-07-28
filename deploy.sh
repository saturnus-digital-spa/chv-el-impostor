#!/bin/sh

ACTION=$1
PROJECT="el-impostor"

# Detect docker-compose command (legacy vs modern plugin)
if command -v docker-compose >/dev/null 2>&1; then
  compose_cmd="docker-compose"
else
  compose_cmd="docker compose"
fi

# Run docker compose
if [ "$ACTION" = "up" ]; then
  $compose_cmd -p $PROJECT up -d --build
elif [ "$ACTION" = "down" ]; then
  $compose_cmd -p $PROJECT down
elif [ "$ACTION" = "nginx" ]; then
  $compose_cmd -p $PROJECT restart nginx
elif [ "$ACTION" = "backend" ] || [ "$ACTION" = "django" ]; then
  $compose_cmd -p $PROJECT restart backend
else
  echo "Action must be \"up\", \"down\", \"nginx\", or \"backend\""
  exit 1
fi