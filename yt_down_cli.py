from argparse import ArgumentParser
import sys
from pathlib import Path
from source.engine import Engine


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument('--video',
                    type=str,
                    required=False,
                    metavar='URL',
                    help='download video')
    parser.add_argument('--playlist',
                        type=str,
                        required=False,
                        metavar='URL',
                        help='download playlist')
    parser.add_argument('--channel',
                        type=str,
                        required=False,
                        metavar='URL',
                        help='download all videos from channel')
    parser.add_argument('--out',
                        type=Path,
                        default='yt_downloaded',
                        help='destination directory')

    args = parser.parse_args()

    eng = Engine()
    if args.video:
        eng.add_video(args.video, dest_dir=args.out)

    if args.playlist:
        eng.add_playlist(args.playlist, dest_dir=args.out)

    if args.channel:
        eng.add_playlist(args.channel, dest_dir=args.out)

    eng.download()

    return 0

if __name__ == '__main__':
    sys.exit(main())
