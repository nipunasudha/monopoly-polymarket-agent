import os
import sys

import pytest

AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    os.chdir(AGENTS_DIR)
    sys.exit(pytest.main(["-p", "no:pytest_ethereum", "tests", *sys.argv[1:]]))
