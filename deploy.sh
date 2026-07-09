#!/bin/bash
# Convenience wrapper for docker deployment
cd "$(dirname "$0")"
exec ./docker/scripts/deploy.sh "$@"
