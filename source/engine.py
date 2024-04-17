from pytube import Playlist, YouTube, Channel, Stream, StreamQuery  # type: ignore
from pathlib import Path
from dataclasses import dataclass
from tqdm import tqdm
from .util import ProgressDownload
import ffmpeg
import shutil


@dataclass
class _VideoInfo:
    url: str
    dest_dir: Path


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
            stream = self._get_highest_resolution(yt.streams)
            assert stream is not None, "Video stream not found"

            if stream.is_progressive:
                self._download_stream(yt, stream, info.dest_dir)
            if stream.is_adaptive:
                self._download_adaptive(yt, stream, yt.streams, info.dest_dir)

    def _init_directory(self, dir: Path) -> None:
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
        if not dir.is_dir():
            raise RuntimeError('Destination has to be a folder')

    def _download_stream(self, yt: YouTube, stream: Stream, dest_dir: Path) -> Path:
        ProgressDownload(yt, stream.filesize)
        return Path(stream.download(output_path=dest_dir))

    def _download_adaptive(self, yt: YouTube, stream: Stream, streams: StreamQuery, dest_dir: Path) -> Path:
        old_video_path = video_path = self._download_stream(
            yt, stream, dest_dir)
        dest_path = video_path.with_suffix('.mkv')
        video_path = video_path.with_stem('video')
        shutil.move(old_video_path, video_path)

        audio_stream = self._get_highest_bitrate_audio(streams)
        assert audio_stream is not None, "Audio stream not found"
        old_audio_path = audio_path = self._download_stream(
            yt, audio_stream, dest_dir)
        audio_path = audio_path.with_stem('audio')
        shutil.move(old_audio_path, audio_path)

        inp_video = ffmpeg.input(str(video_path))
        inp_audio = ffmpeg.input(str(audio_path))
        ffmpeg.concat(inp_video, inp_audio, a=1, v=1) \
            .output(str(dest_path)).run()

        video_path.unlink()
        audio_path.unlink()
        shutil.move(dest_path, video_path)
        return video_path

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
