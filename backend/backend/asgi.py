"""ASGI config for the Django backend project."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_asgi_application()
