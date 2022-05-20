import argparse
from concurrent.futures import as_completed, ThreadPoolExecutor, Future
import csv
import json
from time import sleep
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

from brownie import network
from brownie.network import chain
from tqdm import tqdm

from . import MetadataFacet
from . import StatsFacet
from eth_typing.evm import ChecksumAddress


def unicorn_dnas(
    contract_address: ChecksumAddress,
    token_ids: List[int],
    block_number: Optional[int] = None,
    num_workers: int = 1,
    timeout: float = 30.0,
    checkpoint_file: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if block_number is None:
        block_number = len(chain) - 1

    contract = MetadataFacet.MetadataFacet(contract_address)

    results: List[Dict[str, Any]] = []
    checkpointed_token_ids: Set[int] = set()
    if checkpoint_file is not None:
        with open(checkpoint_file, "r") as ifp:
            for line in ifp:
                stripped_line = line.strip()
                if stripped_line:
                    result = json.loads(stripped_line)
                    if result.get("dna") is not None:
                        results.append(result)
                        checkpointed_token_ids.add(result["token_id"])

    errors: List[Dict[str, Any]] = []

    submission_progress_bar = tqdm(
        total=len(token_ids) - len(checkpointed_token_ids),
        desc="Submitting requests for unicorn DNAs",
    )

    dna_progress_bar = tqdm(
        total=len(token_ids) - len(checkpointed_token_ids),
        desc="Retrieving unicorn DNAs",
    )

    jobs: Dict[Future, int] = {}
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for token_id in token_ids:
            if token_id in checkpointed_token_ids:
                continue
            submission_progress_bar.update()
            future = executor.submit(contract.get_dna, token_id, block_number)
            jobs[future] = token_id

    for future in as_completed(jobs, timeout):
        dna_progress_bar.update()
        token_id = jobs[future]
        try:
            dna = future.result()
            result = {
                "token_id": token_id,
                "block_number": block_number,
                "dna": str(dna),
            }
            results.append(result)
        except Exception as e:
            error = {
                "token_id": token_id,
                "block_number": block_number,
                "error": f"Failed to retrieve DNA: {str(e)}",
            }
            errors.append(error)

    return results, errors


def unicorn_metadata(
    contract_address: ChecksumAddress,
    token_ids: List[int],
    block_number: Optional[int] = None,
    num_workers: int = 1,
    timeout: float = 30.0,
    checkpoint_file: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if block_number is None:
        block_number = len(chain) - 1

    contract = StatsFacet.StatsFacet(contract_address)

    results: List[Dict[str, Any]] = []
    checkpointed_token_ids: Set[int] = set()
    if checkpoint_file is not None:
        with open(checkpoint_file, "r") as ifp:
            for line in ifp:
                stripped_line = line.strip()
                if stripped_line:
                    result = json.loads(stripped_line)
                    if (
                        result.get("class_number") is not None
                        and result.get("lifecycle_stage") is not None
                    ):
                        results.append(result)
                        checkpointed_token_ids.add(result["token_id"])

    errors: List[Dict[str, Any]] = []

    submission_progress_bar = tqdm(
        total=len(token_ids) - len(checkpointed_token_ids),
        desc="Submitting requests for unicorn classes",
    )

    metadata_progress_bar = tqdm(
        total=len(token_ids) - len(checkpointed_token_ids),
        desc="Retrieving unicorn classes",
    )

    jobs: Dict[Future, int] = {}
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for token_id in token_ids:
            if token_id in checkpointed_token_ids:
                continue
            submission_progress_bar.update()
            future = executor.submit(
                contract.get_unicorn_metadata, token_id, block_number
            )
            jobs[future] = token_id

    for future in as_completed(jobs, timeout):
        metadata_progress_bar.update()
        token_id = jobs[future]
        try:
            metadata = future.result()
            result = {
                "token_id": token_id,
                "block_number": block_number,
                "lifecycle_stage": metadata[3],
                "class_number": metadata[-2],
            }
            results.append(result)
        except Exception as e:
            error = {
                "token_id": token_id,
                "block_number": block_number,
                "error": f"Failed to retrieve DNA: {str(e)}",
            }
            errors.append(error)

    return results, errors


def unicorn_mythic_body_parts(
    contract_address: ChecksumAddress,
    dnas: List[Dict[str, Any]],
    block_number: Optional[int] = None,
    num_workers: int = 1,
    timeout: float = 30.0,
    checkpoint_file: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if block_number is None:
        block_number = len(chain) - 1

    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    checkpointed_token_ids: Set[int] = set()
    if checkpoint_file is not None:
        with open(checkpoint_file, "r") as ifp:
            for line in ifp:
                stripped_line = line.strip()
                if stripped_line:
                    result = json.loads(stripped_line)
                    if result.get("num_mythic_body_parts") is not None:
                        results.append(result)
                        checkpointed_token_ids.add(result["token_id"])

    submission_progress_bar = tqdm(
        total=len(dnas) - len(checkpointed_token_ids),
        desc="Submitting requests for number of unicorn mythic body parts",
    )

    mythic_progress_bar = tqdm(
        total=len(dnas) - len(checkpointed_token_ids),
        desc="Retrieving number of unicorn mythic body parts",
    )

    contract = StatsFacet.StatsFacet(contract_address)

    jobs: Dict[Future, int] = {}
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for item in dnas:
            if item["token_id"] in checkpointed_token_ids:
                continue
            submission_progress_bar.update()
            future = executor.submit(
                contract.get_unicorn_body_parts,
                item["dna"],
                item["block_number"],
            )
            jobs[future] = item

    for future in as_completed(jobs, timeout):
        mythic_progress_bar.update()
        item = jobs[future]
        try:
            body_parts = future.result()
            result = {
                **item,
                "num_mythic_body_parts": body_parts[-1],
            }
            results.append(result)
        except Exception as e:
            error = {
                **item,
                "error": f"Failed to retrieve DNA: {str(e)}",
            }
            errors.append(error)

    return results, errors


def handle_dnas(args: argparse.Namespace) -> None:
    network.connect(args.network)
    if args.end is None:
        args.end = args.start
    assert args.start <= args.end, "Starting token ID must not exceed ending token ID"
    token_ids = range(args.start, args.end + 1)
    results, errors = unicorn_dnas(
        args.address,
        token_ids,
        args.block_number,
        args.num_workers,
        args.timeout,
        args.checkpoint,
    )

    for result in results:
        print(json.dumps(result))

    if args.update_checkpoint and args.checkpoint is not None:
        with open(args.checkpoint, "w") as ofp:
            for result in results:
                print(json.dumps(result), file=ofp)

    for error in errors:
        print(json.dumps(error), file=sys.stderr)


def handle_metadata(args: argparse.Namespace) -> None:
    network.connect(args.network)
    if args.end is None:
        args.end = args.start
    assert args.start <= args.end, "Starting token ID must not exceed ending token ID"
    token_ids = range(args.start, args.end + 1)
    results, errors = unicorn_metadata(
        args.address,
        token_ids,
        args.block_number,
        args.num_workers,
        args.timeout,
        args.checkpoint,
    )

    for result in results:
        print(json.dumps(result))

    if args.update_checkpoint and args.checkpoint is not None:
        with open(args.checkpoint, "w") as ofp:
            for result in results:
                print(json.dumps(result), file=ofp)

    for error in errors:
        print(json.dumps(error), file=sys.stderr)


def handle_mythic_body_parts(args: argparse.Namespace) -> None:
    network.connect(args.network)

    dnas: List[Dict[str, Any]] = []
    with open(args.dnas, "r") as ifp:
        for line in ifp:
            dnas.append(json.loads(line.strip()))

    results, errors = unicorn_mythic_body_parts(
        args.address,
        dnas,
        args.block_number,
        args.num_workers,
        args.timeout,
        args.checkpoint,
    )

    for result in results:
        json.dump(result, fp=sys.stdout)
        print("")

    if args.update_checkpoint and args.checkpoint is not None:
        with open(args.checkpoint, "w") as ofp:
            for result in results:
                print(json.dumps(result), file=ofp)

    for error in errors:
        json.dump(error, fp=sys.stderr)
        print("", file=sys.stderr)


def handle_merge(args: argparse.Namespace) -> None:
    metadata_index: Dict[int, Dict[str, Any]] = {}
    mythic_body_parts_index: Dict[int, Dict[str, Any]] = {}

    with open(args.metadata, "r") as metadata_ifp, open(
        args.mythic_body_parts, "r"
    ) as mythic_body_parts_ifp:
        for line in metadata_ifp:
            item = json.loads(line.strip())
            metadata_index[item["token_id"]] = item

        for line in mythic_body_parts_ifp:
            item = json.loads(line.strip())
            mythic_body_parts_index[item["token_id"]] = item

    hidden_classes = {1, 5, 8}
    for token_id, data in metadata_index.items():
        if token_id not in mythic_body_parts_index:
            print(
                f"Token ID in metadata but not in mythic-body-parts: {token_id}",
                file=sys.stderr,
            )
        else:
            mythic_body_parts_data = mythic_body_parts_index[token_id]
            result = {**data, **mythic_body_parts_data}
            del result["block_number"]
            result["metadata_block_number"] = data["block_number"]
            result["mythic_body_parts_block_number"] = mythic_body_parts_data[
                "block_number"
            ]
            if result["lifecycle_stage"] == 0:
                result["num_mythic_body_parts"] = 0
            result["is_mythic"] = result["num_mythic_body_parts"] > 0
            result["is_hidden_class"] = result["class_number"] in hidden_classes
            print(json.dumps(result), file=sys.stdout)


def handle_sob(args: argparse.Namespace) -> None:
    token_metadata_index: Dict[str, Dict[str, Any]] = {}
    with open(args.merged, "r") as ifp:
        for line in ifp:
            item = json.loads(line.strip())
            token_metadata_index[str(item["token_id"])] = item

    moonstream_data: List[Dict[str, Any]] = []
    with open(args.moonstream, "r") as ifp:
        reader = csv.DictReader(ifp)
        for row in reader:
            moonstream_data.append(row)

    breeding_events: List[Dict[str, Any]] = []
    hatching_events: List[Dict[str, Any]] = []

    for event in moonstream_data:
        if event["event_type"] == "breeding":
            event["milestone_1"] = 50
            breeding_events.append(event)
        elif event["event_type"] == "hatchingEggs":
            metadata = token_metadata_index[event["token"]]
            event["milestone_1"] = 0
            if metadata["is_mythic"]:
                event["milestone_1"] = 20
            hatching_events.append(event)
        else:
            # Other conditions in this if statement in the future.
            pass

    player_points: Dict[str, Dict[str, int]] = {}
    for event in breeding_events:
        player = event["player_wallet"]
        if player_points.get(player) is None:
            player_points[player] = {
                "milestone_1": 0,
                "num_breeds": 0,
                "num_hatches": 0,
                "num_mythic_hatches": 0,
            }
        player_points[player]["milestone_1"] += event["milestone_1"]
        player_points[player]["num_breeds"] += 1
    for event in hatching_events:
        player = event["player_wallet"]
        if player_points.get(player) is None:
            player_points[player] = {
                "milestone_1": 0,
                "num_breeds": 0,
                "num_hatches": 0,
                "num_mythic_hatches": 0,
            }
        player_points[player]["milestone_1"] += event["milestone_1"]
        player_points[player]["num_hatches"] += 1
        player_points[player]["num_mythic_hatches"] += int(event["milestone_1"] > 0)

    scores: List[Dict[str, Any]] = []
    for player, points in player_points.items():
        scores.append(
            {
                "address": player,
                "score": points["milestone_1"],
                "points_data": points,
            }
        )

    scores.sort(key=lambda item: item["score"], reverse=True)

    print(json.dumps(scores))


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crypto Unicorns genetics crawler")
    subparsers = parser.add_subparsers()

    dnas_parser = subparsers.add_parser("dnas")
    StatsFacet.add_default_arguments(dnas_parser, False)
    dnas_parser.add_argument(
        "--start",
        type=int,
        required=True,
        help="Starting token ID to get DNA for.",
    )
    dnas_parser.add_argument(
        "--end",
        type=int,
        required=False,
        help="Ending token ID to get DNA for. (If not set, just gets the DNA for the token with the --start token ID.)",
    )
    dnas_parser.add_argument(
        "-j",
        "--num-workers",
        type=int,
        default=1,
        help="Maximum number of concurrent threads to use when crawling",
    )
    dnas_parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=30.0,
        help="Number of seconds to wait for each crawl response",
    )
    dnas_parser.add_argument(
        "--checkpoint",
        default=None,
        help="Checkpoint file",
    )
    dnas_parser.add_argument(
        "-u",
        "--update-checkpoint",
        action="store_true",
        help="If you have set a checkpoint, this updates the checkpoint file in place",
    )

    dnas_parser.set_defaults(func=handle_dnas)

    metadata_parser = subparsers.add_parser("metadata")
    StatsFacet.add_default_arguments(metadata_parser, False)
    metadata_parser.add_argument(
        "--start",
        type=int,
        required=True,
        help="Starting token ID to get DNA for.",
    )
    metadata_parser.add_argument(
        "--end",
        type=int,
        required=False,
        help="Ending token ID to get DNA for. (If not set, just gets the DNA for the token with the --start token ID.)",
    )
    metadata_parser.add_argument(
        "-j",
        "--num-workers",
        type=int,
        default=1,
        help="Maximum number of concurrent threads to use when crawling",
    )
    metadata_parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=30.0,
        help="Number of seconds to wait for each crawl response",
    )
    metadata_parser.add_argument(
        "--checkpoint",
        default=None,
        help="Checkpoint file",
    )
    metadata_parser.add_argument(
        "-u",
        "--update-checkpoint",
        action="store_true",
        help="If you have set a checkpoint, this updates the checkpoint file in place",
    )

    metadata_parser.set_defaults(func=handle_metadata)

    mythic_body_parts_parser = subparsers.add_parser("mythic-body-parts")
    StatsFacet.add_default_arguments(mythic_body_parts_parser, False)
    mythic_body_parts_parser.add_argument(
        "--dnas",
        required=True,
        help='Path to JSON file containing results of "autocorns biologist dnas".',
    )
    mythic_body_parts_parser.add_argument(
        "-j",
        "--num-workers",
        type=int,
        default=1,
        help="Maximum number of concurrent threads to use when crawling",
    )
    mythic_body_parts_parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=30.0,
        help="Number of seconds to wait for each crawl response",
    )
    mythic_body_parts_parser.add_argument(
        "--checkpoint",
        default=None,
        help="Checkpoint file",
    )
    mythic_body_parts_parser.add_argument(
        "-u",
        "--update-checkpoint",
        action="store_true",
        help="If you have set a checkpoint, this updates the checkpoint file in place",
    )

    mythic_body_parts_parser.set_defaults(func=handle_mythic_body_parts)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument(
        "--metadata",
        required=True,
        help='Metadata file generated by "autocorns biologist metadata"',
    )
    merge_parser.add_argument(
        "--mythic-body-parts",
        required=True,
        help='Mythic body parts file generated by "autocorns biologist mythic-body-parts"',
    )

    merge_parser.set_defaults(func=handle_merge)

    sob_parser = subparsers.add_parser("sob")
    sob_parser.add_argument(
        "--merged",
        required=True,
        help='Merged file generated by "autocorns biologist merge"',
    )
    sob_parser.add_argument(
        "--moonstream",
        required=True,
        help="File provided by Moonstream",
    )

    sob_parser.set_defaults(func=handle_sob)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
