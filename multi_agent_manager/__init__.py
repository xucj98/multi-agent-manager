"""Multi-agent task, workspace and process management for the local cluster."""

try:
    from .version import PROGRAM_VERSION
except ImportError:  # Compatibility with a 0.1.0 package copied by old fixtures.
    PROGRAM_VERSION = "0.1.0"

__version__ = PROGRAM_VERSION

__all__ = ["PROGRAM_VERSION", "__version__"]
