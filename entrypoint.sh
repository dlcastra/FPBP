#!/bin/bash

# Function to check service availability
wait_for_service() {
    host=$1
    port=$2
    service_name=$3

    until nc -z -v -w30 $host $port
    do
        echo "Waiting for $service_name connection..."
        sleep 1
    done
}

# Wait for the PostgreSQL service to be ready
wait_for_service $SQL_HOST $SQL_PORT "database"

# Wait for the Redis service to be ready
wait_for_service $REDIS_HOST $REDIS_PORT "Redis"

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start server
daphne -b 0.0.0.0 -p 8000 core.asgi:application
