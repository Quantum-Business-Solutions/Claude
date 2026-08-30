"""Put the linkedin/ directory on sys.path so `qbs_linkedin` imports.

Mirrors contact-verification's flat-script layout: each program is a
self-contained directory rather than a package installed at the repo root.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
