#!/bin/sh
# Install pgvector extension for PostgreSQL 16

set -e

echo "Installing pgvector extension..."

# For Alpine-based PostgreSQL
if command -v apk >/dev/null 2>&1; then
    # Install build dependencies
    apk add --no-cache git build-base postgresql-dev

    # Clone pgvector
    cd /tmp
    git clone --depth 1 --branch v0.5.0 https://github.com/pgvector/pgvector.git
    cd pgvector

    # Build and install
    make
    make install

    # Cleanup
    cd /
    rm -rf /tmp/pgvector

    echo "pgvector installed successfully for Alpine"

# For Debian/Ubuntu-based PostgreSQL
elif command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y git build-essential postgresql-server-dev-16

    cd /tmp
    git clone --depth 1 --branch v0.5.0 https://github.com/pgvector/pgvector.git
    cd pgvector

    make
    make install

    cd /
    rm -rf /tmp/pgvector

    echo "pgvector installed successfully for Debian/Ubuntu"
fi
