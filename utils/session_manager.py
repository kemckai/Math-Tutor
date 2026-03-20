"""
Session state placeholder.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from config import get_settings


@dataclass
class SessionState:
    user_id: int
    username: str
    session_start_ts: float


def get_session_state() -> SessionState:
    """
    Implemented in later step; placeholder to keep app imports consistent.
    """

    settings = get_settings()
    return SessionState(user_id=1, username=settings.default_user, session_start_ts=time.time())

