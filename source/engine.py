from pytube import Playlist, YouTube, Channel, Stream, StreamQuery  # type: ignore
from pathlib import Path
from dataclasses import dataclass
from .util import DownloadCallbackWrapper
import ffmpeg # type: ignore
import shutil
import sys
from typing import Callable, Generator
import re

ALLOWED_CHARS_REGEX = 'a-zA-Z0-9 _,.()'


def _normalize(string: str) -> str:
    return re.sub(f'[^{ALLOWED_CHARS_REGEX}]', lambda x: '_', string)


@dataclass
class _VideoInfo:
    url: str
    dest_dir: Path
    prefix: str


@dataclass
class Callbacks:
    # [file size in bytes]
    on_start: Callable[[int], None] = lambda x: None
    # [percentage 0 ... 1; speed in MB/s]
    on_progress: Callable[[float, float], None] = lambda x, y: None
    # [path to downloaded file]
    on_complete: Callable[[Path], None] = lambda x: None


FFMPEG_PATH = Path(sys.argv[0]).parent/'external'/'ffmpeg.exe'

SUPPORTED_VIDEO_RESOLUTIONS: list[str] = [
    '144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p'
]


def _resolution_to_number(res: str) -> int:
    if res not in SUPPORTED_VIDEO_RESOLUTIONS:
        return -1
    return SUPPORTED_VIDEO_RESOLUTIONS.index(res)


class Engine:
    def __init__(self) -> None:
        self._videos: list[_VideoInfo] = []

    def add_video(self, url: str, dest_dir: Path, *, prefix: str = '') -> None:
        self._videos.append(_VideoInfo(url=url, dest_dir=dest_dir, prefix=prefix))

    def add_playlist(self, url: str, dest_dir: Path, *, create_subdirectory: bool = False, number_entries: bool = False) -> None:
        pl = Playlist(url)
        if create_subdirectory:
            dest_dir /= _normalize(pl.title)

        digits = len(str(len(pl.video_urls) + 1))
        for n, vid in enumerate(pl.video_urls, start=1):
            prefix = ''
            if number_entries:
                prefix = f'{n:0>{digits}}_'
            self.add_video(vid, dest_dir, prefix=prefix)

    def add_channel(self, url: str, dest_dir: Path, *, create_subdirectory: bool = False,  number_entries: bool = False) -> None:
        ch = Channel(url)
        if create_subdirectory:
            dest_dir /= _normalize(ch.channel_name)

        digits = len(str(len(ch.video_urls) + 1))

        for n, vid in enumerate(ch.video_urls, start=1):
            prefix = ''
            if number_entries:
                prefix = f'{n:0>{digits}}_'

            self.add_video(vid, dest_dir, prefix=prefix)

    def video_count(self) -> int:
        return len(self._videos)

    def download(self, *, callbacks: Callbacks | None = None, audio_only: bool = False) -> Generator[Path, None, None]:
        for info in self._videos:
            self._init_directory(info.dest_dir)
            yt = YouTube(info.url)

            if audio_only:
                stream = self._get_highest_bitrate_audio(yt.streams)
                assert stream is not None, 'Audio stream not found'

                file = self._download_stream(yt, stream, info.dest_dir, callbacks)
            else:
                stream = self._get_highest_resolution(yt.streams)
                assert stream is not None, 'Video stream not found'

                if stream.is_progressive:
                    file = self._download_stream(yt, stream, info.dest_dir, callbacks)
                if stream.is_adaptive:
                    file = self._download_adaptive(yt, stream, yt.streams, info.dest_dir, callbacks)

            if info.prefix != '':
                new_file = file.with_stem(info.prefix + file.stem)
                shutil.move(file, new_file)
                file = new_file

            yield file

    def _init_directory(self, dir: Path) -> None:
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
        if not dir.is_dir():
            raise RuntimeError('Destination has to be a folder')

    def _download_stream(self, yt: YouTube, stream: Stream, dest_dir: Path, cbs: Callbacks | None) -> Path:
        wrapp = DownloadCallbackWrapper(yt, stream.filesize)
        if cbs is not None:
            cbs.on_start(stream.filesize)
            wrapp.register_on_progress_callback(cbs.on_progress)
            wrapp.register_on_complete_callback(cbs.on_complete)

        return Path(stream.download(output_path=dest_dir))

    def _download_adaptive(self, yt: YouTube, stream: Stream, streams: StreamQuery, dest_dir: Path, cbs: Callbacks | None) -> Path:
        old_video_path = video_path = self._download_stream(
            yt, stream, dest_dir, cbs)
        dest_path = video_path.with_suffix('.mkv')
        if dest_path.exists():
            dest_path.unlink()

        video_path = video_path.with_stem('video')
        shutil.move(old_video_path, video_path)

        audio_stream = self._get_highest_bitrate_audio(streams)
        assert audio_stream is not None, "Audio stream not found"
        old_audio_path = audio_path = self._download_stream(
            yt, audio_stream, dest_dir, cbs)
        audio_path = audio_path.with_stem('audio')
        shutil.move(old_audio_path, audio_path)

        inp_video = ffmpeg.input(str(video_path))
        inp_audio = ffmpeg.input(str(audio_path))
        target = ffmpeg.output(
            inp_video,
            inp_audio,
            str(dest_path),
            vcodec='copy',
            acodec='copy'
        )
        ffmpeg.run(target, cmd=str(FFMPEG_PATH), quiet=True)

        video_path.unlink()
        audio_path.unlink()
        return dest_path

    def _get_highest_bitrate_audio(self, query: StreamQuery) -> Stream | None:
        streams = sorted(
            query.filter(only_audio=True),
            key=lambda stream: stream.bitrate, reverse=True)

        if len(streams) == 0:
            return None
        return streams[0]

    def _get_highest_resolution(self, query: StreamQuery) -> Stream | None:
        streams = sorted(
            query, key=lambda stream: _resolution_to_number(stream.resolution), reverse=True)

        if len(streams) == 0:
            return None
        return streams[0]
