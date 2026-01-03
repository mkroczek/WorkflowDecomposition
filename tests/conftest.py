from pathlib import Path

import pytest


@pytest.fixture
def resources_dir():
    return Path(__file__).parent / "resources"
