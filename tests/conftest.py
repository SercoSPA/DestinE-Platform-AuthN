"""Pytest configuration.

Ensures the local workspace package is imported during tests.

Some environments may have an older `destinepyauth` installed in site-packages,
which can shadow the sources in this repository. This forces the repository root
onto `sys.path` (highest priority) and clears any already-imported
`destinepyauth*` modules so the tests exercise the current working tree.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# Ensure repo root wins in module resolution.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# If an external destinepyauth is already imported, purge it.
for name in list(sys.modules.keys()):
    if name == "destinepyauth" or name.startswith("destinepyauth."):
        del sys.modules[name]
