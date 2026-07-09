#!/bin/bash
# Convenience wrapper for viewing logs
cd "$(dirname "$0")"
exec ./docker/scripts/logs.sh "$@"
