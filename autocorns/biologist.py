import argparse
from concurrent.futures import as_completed, ThreadPoolExecutor, Future
import json
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


def unicorn_stats(
    contract_address: ChecksumAddress,
    dnas: List[Dict[str, Any]],
    block_number: Optional[int] = None,
    num_workers: int = 1,
    timeout: float = 30.0,
    checkpoint_file: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if block_number is None:
        block_number = len(chain) - 1

    dnas_token_ids: Set[int] = set()
    for result in dnas:
        dnas_token_ids.add(result["token_id"])

    mythic_results: List[Dict[str, Any]] = []
    checkpointed_token_ids: Set[int] = set()
    if checkpoint_file is not None:
        with open(checkpoint_file, "r") as ifp:
            for line in ifp:
                stripped_line = line.strip()
                if stripped_line:
                    result = json.loads(stripped_line)
                    if result["token_id"] not in dnas_token_ids:
                        continue
                    if (
                        result.get("class_number") is not None
                        and result.get("num_mythic_parts") is not None
                    ):
                        mythic_results.append(result)
                        checkpointed_token_ids.add(result["token_id"])

    errors: List[Dict[str, Any]] = []

    contract = StatsFacet.StatsFacet(contract_address)

    metadata_progress_bar = tqdm(
        total=len(dnas_token_ids) - len(checkpointed_token_ids),
        desc="Retrieving unicorn metadata",
    )
    metadata_jobs: Dict[Future, int] = {}
    mythic_jobs: Dict[Future, int] = {}
    num_eggs = 0
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for result in dnas:
            if result["token_id"] in checkpointed_token_ids:
                continue
            future = executor.submit(
                contract.get_unicorn_metadata,
                result["token_id"],
                result["block_number"],
            )
            metadata_jobs[future] = result

        for future in as_completed(metadata_jobs, timeout):
            metadata_progress_bar.update()
            result = metadata_jobs[future]
            try:
                metadata = future.result()
                result["lifecycle_stage"] = metadata[3]
                result["class_number"] = metadata[-2]
                if result["lifecycle_stage"] == 0:
                    result["num_mythic_parts"] = 0
                    mythic_results.append(result)
                    num_eggs += 1
                else:
                    mythic_future = executor.submit(
                        contract.get_unicorn_body_parts,
                        int(result["dna"]),
                        block_number,
                    )
                    mythic_jobs[mythic_future] = result
            except Exception as e:
                error = {
                    "token_id": result["token_id"],
                    "block_number": block_number,
                    "error": f"Failed to retrieve metadata: {str(e)}",
                }
                errors.append(error)

    mythic_progress_bar = tqdm(
        total=len(dnas_token_ids) - len(checkpointed_token_ids) - num_eggs,
        desc="Retrieving number of mythic body parts per unicorn",
    )
    for future in as_completed(mythic_jobs, timeout):
        mythic_progress_bar.update()
        result = mythic_jobs[future]
        try:
            mythic_result = future.result()
            result["num_mythic_parts"] = mythic_result[-1]
            mythic_results.append(result)
        except Exception as e:
            error = {
                "token_id": result["token_id"],
                "block_number": block_number,
                "error": f"Failed to retrieve body part information: {str(e)}",
            }
            errors.append(error)

    return mythic_results, errors


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

    if args.update_checkpoint:
        with open(args.checkpoint, "w") as ofp:
            for result in results:
                print(json.dumps(result), file=ofp)

    for error in errors:
        print(json.dumps(error), file=sys.stderr)


def handle_stats(args: argparse.Namespace) -> None:
    network.connect(args.network)

    dnas: List[Dict[str, Any]] = []
    with open(args.dnas, "r") as ifp:
        for line in ifp:
            dnas.append(json.loads(line.strip()))

    results, errors = unicorn_stats(
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

    for error in errors:
        json.dump(error, fp=sys.stderr)
        print("", file=sys.stderr)


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

    stats_parser = subparsers.add_parser("stats")
    StatsFacet.add_default_arguments(stats_parser, False)
    stats_parser.add_argument(
        "-i",
        "--dnas",
        required=True,
        help='DNAs for unicorns (as produced by "autocorns biologist dnas" command).',
    )
    stats_parser.add_argument(
        "-j",
        "--num-workers",
        type=int,
        default=1,
        help="Maximum number of concurrent threads to use when crawling",
    )
    stats_parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=30.0,
        help="Number of seconds to wait for each crawl response",
    )
    stats_parser.add_argument(
        "--checkpoint",
        default=None,
        help="Checkpoint file",
    )

    stats_parser.set_defaults(func=handle_stats)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
