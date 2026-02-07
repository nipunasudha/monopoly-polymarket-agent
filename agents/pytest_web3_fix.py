"""
Pytest plugin to disable web3 plugin loading before it causes import errors.
"""
import os

# Set this before pytest loads any plugins
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
