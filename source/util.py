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


class ProgressDownload:
    def __init__(self, yt: YouTube, total_size_b: int) -> None:
        self._wrapp = DownloadCallbackWrapper(yt, total_size_b)
        self._last_print_size = 0
        self._total_size_mb = total_size_b / 10**6
        self._print_progress(0.0, 0.0)

        self._wrapp.register_on_progress_callback(self._on_progress_cb)
        self._wrapp.register_on_complete_callback(self._on_complete_cb)

    def _on_progress_cb(self, pct: float, speed: float) -> None:
        self._clear_row()
        self._print_progress(pct * 100.0, speed)

    def _on_complete_cb(self) -> None:
        self._clear_row()

    def _clear_row(self) -> None:
        print('\r', end='', flush=True)
        print(' ' * (self._last_print_size + 1), end='')
        print('\r', end='', flush=True)

    def _print_progress(self, perc: float, speed: float) -> None:
        """
        perc: [0.0 ... 100.0]
        speed: MB/s
        """
        string = self._progress_to_string(perc, speed)
        self._last_print_size = len(string)
        print(string, end='', flush=True)

    def _progress_to_string(self, perc: float, speed: float) -> str:
        """
        perc: [0.0 ... 100.0]
        speed: MB/s
        """
        return f'{perc:.2f} % [{self._total_size_mb * perc / 100.0:.2f} of {self._total_size_mb:.2f} MB] ({speed:.3f} MB/s)'
