from pytube import Playlist, YouTube, Channel  # type: ignore
from pathlib import Path
from dataclasses import dataclass
from tqdm import tqdm


@dataclass
class _VideoInfo:
    url: str
    dest_dir: Path


class Engine:
    def __init__(self) -> None:
        self._videos: list[_VideoInfo] = []

    def add_video(self, url: str, dest_dir: Path) -> None:
        self._videos.append(_VideoInfo(url=url, dest_dir=dest_dir))

    def add_playlist(self, url: str, dest_dir: Path) -> None:
        for vid in Playlist(url).video_urls:
            self.add_video(vid, dest_dir)

    def add_channel(self, url: str, dest_dir: Path) -> None:
        for vid in Channel(url).video_urls:
            self.add_video(vid, dest_dir)

    def download(self) -> None:
        for info in tqdm(self._videos):
            self._init_directory(info.dest_dir)
            yt = YouTube(info.url)
            yt.streams.get_highest_resolution().download(output_path=info.dest_dir)

    def _init_directory(self, dir: Path) -> None:
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
        if not dir.is_dir():
            raise RuntimeError('Destination has to be a folder')
