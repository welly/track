from __future__ import annotations

import re

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
SESSION_ID_PATTERN = re.compile(r"^[0-9a-f]{8}$")
