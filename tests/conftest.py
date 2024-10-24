import os
import sys

import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope='session', autouse=True)
def setup_environment(monkeypatch):
    monkeypatch.setenv('GITHUB_API_KEY', 'test_api_key')

print("HEEEEEEEEEEEEEEY")
