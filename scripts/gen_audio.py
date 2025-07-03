import argparse

from gtts import gTTS
from tqdm import tqdm

from stellarium import constellations


def main():
    parser = argparse.ArgumentParser(
        description="Generate audio files for constellations and objects"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for audio files",
        default="audio",
    )

    subparser = parser.add_subparsers(dest="command")

    subparser.add_parser(
        "constellations", help="Generate audio files for constellations"
    )
    objects = subparser.add_parser("objects", help="Generate audio files for objects")
    new = subparser.add_parser(
        "new", help="Generate an audio file for a stric specified in the command line"
    )

    objects.add_argument(
        "--conf", type=str, help="YAML configuration file with objects", required=True
    )

    new.add_argument("--sound", type=str, help="The sound to generate", required=True)

    new.add_argument(
        "--lang", type=str, help="Target language (e.g., en, es, etc)", default="en"
    )

    args = parser.parse_args()
    if args.command == "constellations":
        for term in tqdm(constellations):
            tts = gTTS(term, lang="la")
            tts.save(f"{args.output_dir}/{term}.mp3")

    elif args.command == "objects":
        with open(args.conf, "r") as f:
            import yaml

            config = yaml.safe_load(f)

        objects = config.get("search").get("objects", [])
        for term in tqdm(objects):
            tts = gTTS(term, lang="en")
            tts.save(f"{args.output_dir}/{term}.mp3")
    elif args.command == "new":
        tts = gTTS(args.sound, lang=args.lang)
        tts.save(f"{args.output_dir}/{args.sound}.mp3")


if __name__ == "__main__":
    main()
