import argparse
import json
import logging
import os
from typing import Any, Dict
import uuid

from brownie import network
import requests

from .biologist import load_checkpoint_data
from .moonstream import get_results_for_moonstream_query
from .ERC721WithDiamondStorage import add_default_arguments, ERC721WithDiamondStorage
from .shadowcorns import crawl, get_rarity, Rarity

logging.basicConfig()
logger = logging.getLogger("autocorns.judge")
log_level = logging.WARN
if os.environ.get("AUTOCORNS_DEBUG") is not None:
    log_level = logging.DEBUG

logger.setLevel(log_level)

if log_level == logging.DEBUG:
    logger.debug(f"DEBUG mode")


def handle_throwing_shade(args: argparse.Namespace) -> None:
    moonstream_access_token = os.environ.get("MOONSTREAM_ACCESS_TOKEN")
    if moonstream_access_token is None:
        raise ValueError("Please set the MOONSTREAM_ACCESS_TOKEN environment variable")

    logger.debug(
        f"Retrieving results for Moonstream Query: api={args.query_api}, query={args.query_name}"
    )
    params: Dict[str, Any] = {}
    query_results = get_results_for_moonstream_query(
        moonstream_access_token,
        args.query_name,
        params,
        args.query_api,
        args.max_retries,
        args.interval,
    )

    leaderboard = query_results.get("data", [])
    engine_api = args.engine_api.rstrip("/")
    leaderboard_api = f"{engine_api}/leaderboard/{str(args.leaderboard_id)}/scores"
    headers = {
        "Authorization": f"Bearer {moonstream_access_token}",
        "Content-Type": "application/json",
    }
    query_params = {"normalize_addresses": "false"}

    logger.debug(
        f"Getting Shadowcorn rarity information for multipliers. Using metadata file: {args.metadata}."
    )
    multipliers: Dict[str, float] = {}
    network.connect(args.network)
    shadowcorns = ERC721WithDiamondStorage(args.address)
    checkpoint_data = load_checkpoint_data(args.metadata)
    new_metadata, _ = crawl(shadowcorns, checkpoint_data)
    with open("temp.json", "w") as ofp:
        for item in new_metadata + checkpoint_data:
            rarity = get_rarity(item)
            multiplier = 1.0
            if rarity == Rarity.rare:
                multiplier = 1.2
            elif rarity == Rarity.mythic:
                multiplier = 1.5
            multipliers[str(item["token_id"])] = multiplier
            item["rarity"] = rarity.value
            item["multiplier"] = multiplier
            print(json.dumps(item), file=ofp)

    with open(args.metadata, "w") as ofp:
        for result in new_metadata + checkpoint_data:
            print(json.dumps(result), file=ofp)

    logger.debug("Applying multipliers")
    for row in leaderboard:
        row_multiplier = multipliers[row["address"]]
        row["points_data"]["rarity_multiplier"] = str(row_multiplier)
        row["score"] = str(int(row_multiplier * float(row["score"])))

    logger.debug(f"Pushing leaderboard: {leaderboard_api}")
    response = requests.put(
        leaderboard_api, headers=headers, json=leaderboard, params=query_params
    )
    response.raise_for_status()
    logger.debug("Done!")


def generate_cli() -> argparse.ArgumentParser:
    """
    Generates an argument parser for the "autocorns judge" command.
    """
    parser = argparse.ArgumentParser(
        description="The Judge: Generates Crypto Unicorns leaderboards"
    )
    parser.set_defaults(func=lambda _: parser.print_help())
    subparsers = parser.add_subparsers()

    shadowcorns_throwing_shade_parser = subparsers.add_parser(
        "throwing-shade", description="Shadowcorns: Throwing Shade Leaderboard"
    )
    shadowcorns_throwing_shade_parser.add_argument(
        "--query-api",
        default="https://api.moonstream.to",
        help="Moonstream API URL. Access token expected to be set as MOONSTREAM_ACCESS_TOKEN environment variable.",
    )
    shadowcorns_throwing_shade_parser.add_argument(
        "--query-name",
        default="Shadowcorns_Throwing_Shade_Leaderboard",
        help="Name of Moonstream Query API query to use to generate the Shadowcorns: Throwing Shade leaderboard",
    )
    shadowcorns_throwing_shade_parser.add_argument(
        "--engine-api",
        default="https://engineapi.moonstream.to",
        help="Moonstream Engine API URL. Access token expected to be set as MOONSTREAM_ACCESS_TOKEN environment variable.",
    )
    shadowcorns_throwing_shade_parser.add_argument(
        "--leaderboard-id",
        type=uuid.UUID,
        required=True,
        help="Leaderboard ID on Engine API",
    )
    shadowcorns_throwing_shade_parser.add_argument(
        "--max-retries",
        type=int,
        default=100,
        help="Number of times to retry requests for Moonstream Query results",
    )
    shadowcorns_throwing_shade_parser.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Number of seconds to wait between attempts to get results from Moonstream Query API",
    )
    add_default_arguments(shadowcorns_throwing_shade_parser, False)
    shadowcorns_throwing_shade_parser.add_argument(
        "--metadata",
        required=True,
        help='File containing Shadowcorn metadata (in same format as "autocorns shadowcorns crawl")',
    )
    shadowcorns_throwing_shade_parser.set_defaults(func=handle_throwing_shade)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
