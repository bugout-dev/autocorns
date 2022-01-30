import argparse

from . import DarkForest

def main():
    parser = argparse.ArgumentParser(description="autocorns: Crypto Unicorns automation")
    parser.set_defaults(func=lambda _: parser.print_help())
    subparsers = parser.add_subparsers()

    dark_forest_parser = DarkForest.generate_cli()
    subparsers.add_parser("dark-forest", parents=[dark_forest_parser], add_help=False)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
