import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from helpers import Fx  # noqa: E402


@pytest.fixture
def fx(tmp_path):
    return Fx(tmp_path)
