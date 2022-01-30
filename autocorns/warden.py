"""
The warden leads unicorns safely through the Dark Forest.
"""

import argparse
import json
import os
import time
from typing import List, Tuple

from brownie import network

from . import DarkForest, ERC721

CU_MAINNET_ADDRESS = "0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f"
DARK_FOREST_MAINNET_ADDRESS = "0x8d528e98A69FE27b11bb02Ac264516c4818C3942"

BROWNIE_NETWORK = os.environ.get("BROWNIE_NETWORK", "matic")
DARK_FOREST_ADDRESS = os.environ.get("DARK_FOREST_ADDRESS", DARK_FOREST_MAINNET_ADDRESS)
CU_ADDRESS = os.environ.get("DARK_FOREST_ADDRESS", CU_MAINNET_ADDRESS)


def escort(corns: List[int], transaction_config) -> List[int]:
    """
    Unstakes all unstakable unicorns for the given player.
    Then stakes all stakable unicorns for the given player.

    Return list of staked corns.
    """
    print(
        f"Network: {BROWNIE_NETWORK}, Crypto Unicorns: {CU_ADDRESS}, Dark Forest: {DARK_FOREST_ADDRESS}"
    )
    network.connect(BROWNIE_NETWORK)

    nonce = None
    if transaction_config.get("nonce"):
        nonce = transaction_config["nonce"] - 1

    unstaked: List[int] = []
    staked: List[Tuple[int, int]] = []

    crypto_unicorns = ERC721.ERC721(CU_ADDRESS)
    dark_forest = DarkForest.DarkForest(DARK_FOREST_ADDRESS)

    for corn in corns:
        unstakes_at = dark_forest.unstakes_at(corn)
        if unstakes_at > 0:
            staked.append((corn, unstakes_at))
        else:
            unstaked.append(corn)

    time_now = int(time.time())
    print(f"Machine time: {time_now}")
    staked_final: List[int] = []
    ready_to_unstake: List[int] = []

    for corn, unstakes_at in staked:
        if unstakes_at <= time_now:
            ready_to_unstake.append(corn)
        else:
            staked_final.append(corn)

    for corn in ready_to_unstake:
        if nonce is not None:
            nonce += 1
            transaction_config["nonce"] = nonce
        dark_forest.exit_forest(corn, transaction_config)
        unstaked.append(corn)

    player = transaction_config["from"].address
    for corn in unstaked:
        if nonce is not None:
            nonce += 1
            transaction_config["nonce"] = nonce
        crypto_unicorns.safe_transfer_from(
            player, DARK_FOREST_ADDRESS, corn, b"", transaction_config
        )
        staked_final.append(corn)

    return staked_final


def handle_escort(args: argparse.Namespace) -> None:
    transaction_config = DarkForest.get_transaction_config(args)
    staked_corns = escort(args.corns, transaction_config)
    print(json.dumps(staked_corns))


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="The Dark Forest warden")

    DarkForest.add_default_arguments(parser, True)
    parser.add_argument(
        "--corns",
        nargs="+",
        type=int,
        help="List of corns to escort into or out of the Dark Forest",
    )

    parser.set_defaults(func=handle_escort)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
