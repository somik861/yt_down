from pytube import YouTube, Stream  # type: ignore
from pathlib import Path
from datetime import datetime
from typing import Callable


class DownloadCallbackWrapper:
    def __init__(self, yt: YouTube, total_size_b: int) -> None:
        self._yt = yt.register_on_progress_callback(self._on_progress_cb)
        self._yt = yt.register_on_complete_callback(self._on_complete_cb)
        self._on_progress_cbs: list[Callable[[float, float], None]] = []
        self._on_complete_cbs: list[Callable[[], None]] = []
        self._total_size_b = self._delta_remaining_bytes = total_size_b
        self._delta_start = datetime.now()

    def register_on_progress_callback(self, cb: Callable[[float, float], None]) -> None:
        """cb ([0...1, MB/s])"""
        self._on_progress_cbs.append(cb)

    def register_on_complete_callback(self, cb: Callable[[], None]) -> None:
        self._on_complete_cbs.append(cb)

    def _on_progress_cb(self, stream: Stream, chunk: bytes, remaning_bytes: int) -> None:
        delta_t = datetime.now() - self._delta_start
        delta_mb = (self._delta_remaining_bytes - remaning_bytes) / 10**6

        for cb in self._on_progress_cbs:
            cb(1.0 - (remaning_bytes/self._total_size_b),
               delta_mb / delta_t.total_seconds())

        self._delta_start = datetime.now()
        self._delta_remaining_bytes = remaning_bytes

    def _on_complete_cb(self, stream: Stream, path: Path) -> None:
        for cb in self._on_complete_cbs:
            cb()
