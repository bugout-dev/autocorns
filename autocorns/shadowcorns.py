import argparse
import base64
import enum
import json
import time
from typing import Any, Dict, List

from brownie import network
from tqdm import tqdm

from .biologist import load_checkpoint_data, make_multicall
from .ERC721 import ERC721, add_default_arguments
from .ERC721WithDiamondStorage import ERC721WithDiamondStorage
from . import Multicall2

METADATA_PREFIX = "data:application/json;base64,"


class Rarity(enum.Enum):
    unknown = "unknown"
    common = "common"
    rare = "rare"
    mythic = "mythic"


RARITY_VALUES = {item.value for item in list(Rarity)}

MULTICALL2_ADDRESS = "0xc8E51042792d7405184DfCa245F2d27B94D013b6"
CALL_CHUNK_SIZE = 500


def parse_shadowcorn_metadata(encoded_metadata: str) -> Dict[str, Any]:
    assert encoded_metadata.startswith(
        METADATA_PREFIX
    ), f"Unexpected metadata:\n{encoded_metadata}"
    decoded_metadata = base64.b64decode(encoded_metadata[len(METADATA_PREFIX) :])
    metadata = json.loads(decoded_metadata)
    return metadata


def rarity(shadowcorn_metadata: Dict[str, Any]) -> Rarity:
    attributes = shadowcorn_metadata.get("attributes", [])
    rarity_value = Rarity.unknown
    for attribute in attributes:
        if attribute.get("trait_type", "").lower() == "rarity":
            rarity_value = Rarity(attribute["value"].lower())

    return rarity_value


def handle_metadata(args: argparse.Namespace) -> None:
    network.connect(args.network)
    shadowcorns = ERC721(args.address)
    token_uri: str = shadowcorns.token_uri(args.token_id)
    metadata = parse_shadowcorn_metadata(token_uri)
    print(json.dumps(metadata))


def handle_crawl(args: argparse.Namespace) -> None:
    network.connect(args.network)
    checkpoint_data = []
    if args.checkpoint:
        checkpoint_data = load_checkpoint_data(args.checkpoint)

    shadowcorns = ERC721WithDiamondStorage(args.address)
    current_supply = shadowcorns.total_supply()

    existing_token_ids = [item["token_id"] for item in checkpoint_data]

    token_ids_to_crawl = [
        i for i in range(1, current_supply + 1) if i not in existing_token_ids
    ]

    results: List[Dict[str, Any]] = []

    errors: List[Dict[str, Any]] = []

    token_uris = []

    progress_bar = tqdm(
        total=len(token_ids_to_crawl),
        desc="Retrieving new Shadowcorn metadata",
    )

    multicaller = Multicall2.Multicall2(MULTICALL2_ADDRESS)

    multicall_method = multicaller.contract.tryAggregate

    for tokens_ids_chunk in [
        token_ids_to_crawl[i : i + CALL_CHUNK_SIZE]
        for i in range(0, len(token_ids_to_crawl), CALL_CHUNK_SIZE)
    ]:
        while True:
            try:
                make_multicall_result = make_multicall(
                    multicall_method,
                    shadowcorns.contract.tokenURI,
                    args.address,
                    tokens_ids_chunk,
                )
                token_uris.extend(make_multicall_result)
                progress_bar.update(len(tokens_ids_chunk))
                break
            except ValueError:
                time.sleep(1)
                continue

    for token_id, uri in zip(token_ids_to_crawl, token_uris):
        try:
            result = {
                "token_id": token_id,
                "metadata": parse_shadowcorn_metadata(uri),
                "uri": uri,
            }
            results.append(result)
        except Exception as e:
            error = {"token_id": token_id, "uri": uri}
            errors.append(error)

    if args.checkpoint:
        with open(args.checkpoint, "w") as ofp:
            for result in results + checkpoint_data:
                print(json.dumps(result), file=ofp)
    else:
        for result in results:
            print(json.dumps(result))


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shadowcorn utilities")
    parser.set_defaults(func=lambda _: parser.print_help())

    subparsers = parser.add_subparsers()

    metadata_parser = subparsers.add_parser("metadata")
    add_default_arguments(metadata_parser, False)
    metadata_parser.add_argument(
        "-i", "--token-id", required=True, type=int, help="Shadowcorn token ID"
    )
    metadata_parser.set_defaults(func=handle_metadata)

    crawl_parser = subparsers.add_parser("crawl")
    add_default_arguments(crawl_parser, False)
    crawl_parser.add_argument(
        "--checkpoint", default=None, help="Checkpoint file (optional)"
    )
    crawl_parser.set_defaults(func=handle_crawl)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
