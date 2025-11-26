#!/bin/bash
# Script to create test data inside Docker container

echo "Creating test data in Docker container..."
docker-compose exec -T backend python3 scripts/create_test_data.py

