"""A minimal stand-in for the body of an aiohttp response."""

from __future__ import annotations

from collections.abc import AsyncIterator


class FakeContent:
    """What ``resp.content`` offers the client: the body in chunks."""

    def __init__(self, body: str | bytes) -> None:
        self._body = body.encode("latin-1", errors="replace") if isinstance(body, str) else body

    async def iter_chunked(self, size: int) -> AsyncIterator[bytes]:
        """Yield the body in chunks of at most ``size`` bytes."""
        for start in range(0, len(self._body), size):
            yield self._body[start : start + size]
