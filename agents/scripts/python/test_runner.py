import os
import sys

import pytest

AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Run tests with web3 plugin disabled to avoid import errors."""
    os.chdir(AGENTS_DIR)
    
    # Disable plugin autoload to avoid web3 import issues
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    
    # Run pytest with web3 and pytest_ethereum plugins disabled
    sys.exit(pytest.main(["-p", "no:web3", "-p", "no:pytest_ethereum", "tests", *sys.argv[1:]]))
