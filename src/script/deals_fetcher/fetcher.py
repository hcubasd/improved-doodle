from collections.abc import Callable, Awaitable

type RawRecord = dict[str, object]
type FetchParams = dict[str, object] | None
type FetchResult = tuple[list[RawRecord], bool]
type Fetcher = Callable[[str, FetchParams], Awaitable[FetchResult]]
