from argparse import ArgumentParser
import sys
from pathlib import Path
from source.engine import Engine, Callbacks
from source.cli_util import ProgressDownload
from tqdm import tqdm


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument('--videos',
                        type=str,
                        required=False,
                        metavar='URL',
                        nargs='*',
                        help='download videos')
    parser.add_argument('--playlists',
                        type=str,
                        required=False,
                        metavar='URL',
                        nargs='*',
                        help='download playlists')
    parser.add_argument('--channels',
                        type=str,
                        required=False,
                        metavar='URL',
                        nargs='*',
                        help='download all videos from channels')
    parser.add_argument('--out',
                        type=Path,
                        default='yt_downloaded',
                        help='destination directory')
    parser.add_argument('--disable_subdirs',
                        action='store_true',
                        help='Disable video sorting into subdirectories according to channel/playlist')

    parser.add_argument('--disable_numbering',
                        action='store_true',
                        help='Disable numbering of videos from channel and playlist')

    args = parser.parse_args()

    eng = Engine()
    if args.videos:
        for video in args.videos:
            eng.add_video(video, dest_dir=args.out)

    if args.playlists:
        for playlist in args.playlists:
            eng.add_playlist(playlist, dest_dir=args.out, create_subdirectory=(not args.disable_subdirs), number_entries=(not args.disable_numbering))

    if args.channels:
        for channel in args.channels:
            eng.add_playlist(channel, dest_dir=args.out, create_subdirectory=(not args.disable_subdirs), number_entries=(not args.disable_numbering))

    cbs = Callbacks()
    ProgressDownload(cbs)
    for _ in tqdm(eng.download(cbs), total=eng.video_count()):
        pass

    return 0


if __name__ == '__main__':
    sys.exit(main())
