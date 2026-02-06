#!/bin/bash
# Simple test runner script that handles web3 plugin issue

# Set environment variable to disable plugin autoload
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

# Run pytest with web3 plugin disabled
uv run pytest "$@" -p no:web3
