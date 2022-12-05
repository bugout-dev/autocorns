import argparse

from . import warden, biologist, crawl_reports, judge, shadowcorns


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

    judge_parser = judge.generate_cli()
    subparsers.add_parser("judge", parents=[judge_parser], add_help=False)

    shadowcorns_parser = shadowcorns.generate_cli()
    subparsers.add_parser("shadowcorns", parents=[shadowcorns_parser], add_help=False)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
