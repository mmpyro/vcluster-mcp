"""Pytest configuration for vcluster-mcp-server tests."""

import sys
import os

# Add the src directory to the Python path so we can import utils.* directly
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
