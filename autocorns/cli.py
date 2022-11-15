import argparse

from . import warden, biologist, crawl_reports, dark_altar


def main():
    parser = argparse.ArgumentParser(
        description="autocorns: Crypto Unicorns automation"
    )
    parser.set_defaults(func=lambda _: parser.print_help())
    subparsers = parser.add_subparsers()

    warden_parser = warden.generate_cli()
    subparsers.add_parser("warden", parents=[warden_parser], add_help=False)

    biologist_parser = biologist.generate_cli()
    subparsers.add_parser("biologist", parents=[biologist_parser], add_help=False)

    crawler_parser = crawl_reports.generate_cli()
    subparsers.add_parser("dna-reports", parents=[crawler_parser], add_help=False)

    dark_altar_parser = dark_altar.generate_cli()
    subparsers.add_parser("dark-altar", parents=[dark_altar_parser], add_help=False)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
