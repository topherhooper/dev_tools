import argparse
import aetheris
import talmorion
import deemer

BOT_MAP = {
    aetheris.Aetheris.name: aetheris.Aetheris,
    talmorion.Talmorion.name: talmorion.Talmorion,
    deemer.Deemer.name: deemer.Deemer,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bot",
        choices=BOT_MAP.keys(),
        help="Bot options: " + ", ".join(BOT_MAP.keys()),
        metavar="",
    )
    args = parser.parse_args()

    print(args.bot)
    brain_bot = BOT_MAP[args.bot]()
    brain_bot.run()


if __name__ == "__main__":
    main()
