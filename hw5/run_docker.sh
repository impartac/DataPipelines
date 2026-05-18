#!/bin/bash
# Script to run Spark benchmarks in Docker

set -e

echo "=========================================="
echo "Spark Performance Benchmark - Docker Runner"
echo "=========================================="
echo ""

# Parse command line arguments
SIZE=${1:-small}

case $SIZE in
  small)
    echo "Running SMALL benchmark (10,000 rows)..."
    docker-compose up spark-benchmark
    ;;
  medium)
    echo "Running MEDIUM benchmark (100,000 rows)..."
    docker-compose --profile medium up spark-benchmark-medium
    ;;
  large)
    echo "Running LARGE benchmark (1,000,000 rows)..."
    docker-compose --profile large up spark-benchmark-large
    ;;
  *)
    echo "Invalid size: $SIZE"
    echo "Usage: $0 [small|medium|large]"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "Benchmark completed!"
echo "Check ./reports/ directory for results"
echo "=========================================="
