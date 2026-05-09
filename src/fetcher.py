from collections.abc import Callable, Awaitable

Fetcher = Callable[[str, dict | None], Awaitable[tuple[list[dict], bool]]]
