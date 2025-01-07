#!/bin/bash

# Check if a file argument is provided
if [ $# -eq 0 ]; then
    echo "No file provided. Usage: $0 <python_file>" >&2
    exit 1
fi

file="$1"

# Run formatters silently
poetry run black --quiet --config pyproject.toml "$file"
poetry run isort --quiet --settings-path pyproject.toml "$file"
poetry run autoflake --quiet --remove-all-unused-imports --in-place "$file"

# Set Pyright version to latest
export PYRIGHT_PYTHON_FORCE_VERSION=latest

# Run Pyright and output its results
poetry run pyright "$file"

# The exit code will be the exit code of the last command (pyright)
