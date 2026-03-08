from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Key = client IP by default
limiter = Limiter(key_func=get_remote_address)