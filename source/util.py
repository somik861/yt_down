from pytube import YouTube, Stream  # type: ignore
from pathlib import Path
from datetime import datetime


class ProgressDownload:
    def __init__(self, yt: YouTube, total_size_b: int) -> None:
        self._yt = yt.register_on_progress_callback(self._on_progress_update)
        self._yt = yt.register_on_complete_callback(self._on_complete_update)
        self._total_size_b = total_size_b
        self._print_progress(0.0, 0.0)
        self._delta_start = datetime.now()
        self._delta_remaining_bytes = 0.0

    def _on_progress_update(self, stream: Stream, chunk: bytes, remaning_bytes: int) -> None:
        self._clear_row()
        delta_t = datetime.now() - self._delta_start
        delta_mb = (self._delta_remaining_bytes - remaning_bytes) / 10**6

        self._print_progress((1.0 - (remaning_bytes/self._total_size_b)) * 100.0, max(delta_mb / delta_t.total_seconds(), 0.0))

        self._delta_start = datetime.now()
        self._delta_remaining_bytes = remaning_bytes

    def _on_complete_update(self, stream: Stream, path: Path) -> None:
        self._clear_row()

    def _clear_row(self) -> None:
        print('\r', end='')

    def _print_progress(self, perc: float, speed: float) -> None:
        """
        perc: [0.0 ... 100.0]
        speed: MB/s
        """
        print(self._progress_to_string(perc, speed), end='', flush=True)

    def _progress_to_string(self, perc: float, speed: float) -> str:
        """
        perc: [0.0 ... 100.0]
        speed: MB/s
        """
        return f'{perc:.2f} ({speed} MB/s)'
