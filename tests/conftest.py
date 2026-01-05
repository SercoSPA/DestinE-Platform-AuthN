"""Pytest configuration.

Ensure tests import the local working tree package.

Some environments may have an installed `destinepyauth` that can shadow the
repository sources. Adding the repository root to `sys.path` ensures `import
destinepyauth` resolves to this checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
