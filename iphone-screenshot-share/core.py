from __future__ import annotations

import os
from datetime import datetime


def is_allowed(chat_id, allowlist):
    """True only if allowlist is non-empty AND chat_id is in it.

    An empty allowlist means 'setup mode': nothing is accepted yet.
    """
    return bool(allowlist) and chat_id in allowlist
