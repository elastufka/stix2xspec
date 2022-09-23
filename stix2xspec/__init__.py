# type: ignore[attr-defined]
"""Convert STIX science data (L1A, L1, or L4 spectrograms or pixel data) to a format compatible with XSPEC"""

import sys

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()
