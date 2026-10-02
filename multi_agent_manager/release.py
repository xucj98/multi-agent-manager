"""Source metadata embedded in release archives.

``git archive`` expands the commit placeholder because this file is marked
with ``export-subst`` in ``.gitattributes``.  A checkout still reports its
current commit dynamically.
"""

RELEASE_VERSION = "0.2.3"
RELEASE_TAG = "v0.2.3"
RELEASE_COMMIT = "$Format:%H$"
