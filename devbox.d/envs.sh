#!/bin/bash

ELEVEN_API_KEY=$(cat ~/.config/elevenlabs/key)
export ELEVEN_API_KEY

ASSEMBLYAI_API_KEY=$(cat ~/.config/assemblyai/key)
export ASSEMBLYAI_API_KEY

FIRECRAWL_API_KEY=$(cat ~/.config/firecrawl/key)
export FIRECRAWL_API_KEY

AI_ASSISTANT_HUMAN_NAME=$(cat ~/.config/pulumipus/human_name)
export AI_ASSISTANT_HUMAN_NAME

AI_ASSISTANT_NAME=$(cat ~/.config/pulumipus/assistant_name)
export AI_ASSISTANT_NAME

UV_PYTHON=$DEVBOX_PROJECT_ROOT/.venv/bin/python
export UV_PYTHON
