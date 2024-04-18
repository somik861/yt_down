from .engine import Callbacks


class ProgressDownload:
    def __init__(self, cbs: Callbacks) -> None:
        cbs.on_start = self._on_start_cb
        cbs.on_progress = self._on_progress_cb
        cbs.on_complete = self._on_complete_cb

    def _on_start_cb(self, total_size_b: int) -> None:
        self._last_print_size = 0
        self._total_size_mb = total_size_b / 10**6
        self._print_progress(0.0, 0.0)

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
