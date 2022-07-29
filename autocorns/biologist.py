import argparse
import datetime
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple


from brownie import network, web3
from brownie.network import chain
import requests
from tqdm import tqdm

from . import ERC721WithDiamondStorage
from . import MetadataFacet
from . import Multicall2
from . import StatsFacet
from eth_typing.evm import ChecksumAddress


CALL_CHUNK_SIZE = 500


Multicall2_address = "0xc8E51042792d7405184DfCa245F2d27B94D013b6"


def make_multicall(
    multicall_method: Any,
    brownie_contract_method: Any,
    address: web3.toChecksumAddress,
    inputs: List[Any],
    block_number: str = "latest",
) -> Any:
    multicall_result = multicall_method.call(
        False,  # success not required
        [
            (
                address,
                brownie_contract_method.encode_input(input),
            )
            for input in inputs
        ],
        block_identifier=block_number,
    )

    results = []

    # Handle the case with not successful calls
    for encoded_data in multicall_result:
        if encoded_data[0]:
            results.append(brownie_contract_method.decode_output(encoded_data[1]))
        else:
            print(encoded_data, file=sys.stderr)
            results.append(None)
    return results


def unicorn_dnas(
    contract_address: ChecksumAddress,
    token_ids: List[int],
    block_number: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if block_number is None:
        block_number = len(chain) - 1

    contract = MetadataFacet.MetadataFacet(contract_address)

    results: List[Dict[str, Any]] = []

    errors: List[Dict[str, Any]] = []

    tokens_dnas = []

    dna_progress_bar = tqdm(
        total=len(token_ids),
        desc="Retrieving unicorn DNAs",
    )

    CALL_CHUNK_SIZE_DNA = CALL_CHUNK_SIZE

    multicaller = Multicall2.Multicall2(Multicall2_address)

    multicall_method = multicaller.contract.tryAggregate
    # multicall_method = multicaller.contract.aggregate

    for tokens_ids_chunk in [
        token_ids[i : i + CALL_CHUNK_SIZE_DNA]
        for i in range(0, len(token_ids), CALL_CHUNK_SIZE_DNA)
    ]:
        while True:
            try:
                make_multicall_result = make_multicall(
                    multicall_method,
                    contract.contract.getDNA,
                    contract_address,
                    tokens_ids_chunk,
                    block_number=block_number,
                )
                tokens_dnas.extend(make_multicall_result)
                dna_progress_bar.update(len(tokens_ids_chunk))
                break
            except ValueError:
                time.sleep(1)
                continue

    for token_id, token_dna in zip(token_ids, tokens_dnas):
        try:
            result = {
                "token_id": token_id,
                "block_number": block_number,
                "dna": str(token_dna),
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
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if block_number is None:
        block_number = len(chain) - 1

    contract = StatsFacet.StatsFacet(contract_address)

    results: List[Dict[str, Any]] = []

    errors: List[Dict[str, Any]] = []

    tokens_metadata = []

    calls_progress_bar = tqdm(
        total=len(token_ids),
        desc="Submitting requests for unicorn classes",
    )

    multicaller = Multicall2.Multicall2(Multicall2_address)

    multicall_method = multicaller.contract.tryAggregate

    for tokens_ids_chunk in [
        token_ids[i : i + CALL_CHUNK_SIZE]
        for i in range(0, len(token_ids), CALL_CHUNK_SIZE)
    ]:
        while True:
            try:
                make_multicall_result = make_multicall(
                    multicall_method,
                    contract.contract.getUnicornMetadata,
                    contract_address,
                    tokens_ids_chunk,
                    block_number=block_number,
                )
                tokens_metadata.extend(make_multicall_result)
                calls_progress_bar.update(len(tokens_ids_chunk))
                break
            except ValueError:
                time.sleep(1)
                continue

    for token_id, token_data in zip(token_ids, tokens_metadata):
        try:
            result = {
                "token_id": token_id,
                "block_number": block_number,
                "lifecycle_stage": token_data[3],
                "class_number": token_data[-2],
            }
            results.append(result)
        except Exception as e:
            error = {
                "token_id": token_id,
                "block_number": block_number,
                "error": f"Failed retrive unicorns metadata: {str(e)}",
            }
            errors.append(error)
    return results, errors


def unicorn_mythic_body_parts(
    contract_address: ChecksumAddress,
    dnas: List[Dict[str, Any]],
    block_number: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if block_number is None:
        block_number = len(chain) - 1

    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    tokens_metadata = []

    mythic_progress_bar = tqdm(
        total=len(dnas),
        desc="Retrieving number of unicorn mythic body parts",
    )

    contract = StatsFacet.StatsFacet(contract_address)

    block_number = dnas[0]["block_number"]

    multicaller = Multicall2.Multicall2(Multicall2_address)

    multicall_method = multicaller.contract.tryAggregate

    dnas_is_present = [
        dna for dna in dnas if dna["dna"] is not None and dna["dna"] != "None"
    ]

    for dnas_chunk in [
        dnas_is_present[i : i + CALL_CHUNK_SIZE]
        for i in range(0, len(dnas), CALL_CHUNK_SIZE)
    ]:
        while True:
            try:

                send_to_multicall_dnas = [dna["dna"] for dna in dnas_chunk]

                make_multicall_result = make_multicall(
                    multicall_method,
                    contract.contract.getUnicornBodyParts,
                    contract_address,
                    send_to_multicall_dnas,
                    block_number=block_number,
                )
                tokens_metadata.extend(make_multicall_result)
                mythic_progress_bar.update(len(send_to_multicall_dnas))
                break
            except ValueError:
                time.sleep(1)
                continue
            except Exception as e:
                print(e, file=sys.stderr)
                print(send_to_multicall_dnas, file=sys.stderr)
                raise e

    for item, token_data in zip(dnas_is_present, tokens_metadata):
        if token_data is None:
            # Token item['token_id']} has no DNA
            continue
        try:
            result = {
                **item,
                "num_mythic_body_parts": token_data[-1],
            }
            results.append(result)
        except Exception as e:
            error = {
                **item,
                "error": f"Failed to retrieve num_mythic_body_parts: {str(e)}",
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
    )

    for result in results:
        print(json.dumps(result))

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
    )

    for result in results:
        print(json.dumps(result))

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
    )

    for result in results:
        json.dump(result, fp=sys.stdout)
        print("")

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
            if (
                mythic_body_parts_data.get("num_mythic_body_parts") is None
                and result["lifecycle_stage"] == 0
            ):
                result["num_mythic_body_parts"] = 0
            if mythic_body_parts_data.get("num_mythic_body_parts") == 6:
                result["num_mythic_body_parts"] = 0
            result["is_mythic"] = result["num_mythic_body_parts"] > 0
            result["is_hidden_class"] = result["class_number"] in hidden_classes
            print(json.dumps(result), file=sys.stdout)


def handle_moonstream_events(args: argparse.Namespace) -> None:
    moonstream_access_token = os.environ.get("MOONSTREAM_ACCESS_TOKEN")
    if moonstream_access_token is None:
        raise ValueError("Please set the MOONSTREAM_ACCESS_TOKEN environment variable")

    api_url = args.api.rstrip("/")
    request_url = f"{api_url}/queries/{args.query_name}/update_data"
    headers = {
        "Authorization": f"Bearer {moonstream_access_token}",
        "Content-Type": "application/json",
    }
    # Assume our clock is not drifting too much from AWS clocks.
    if_modified_since_datetime = datetime.datetime.utcnow()
    if_modified_since = if_modified_since_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
    end_timestamp = int(time.time())
    if args.end is not None:
        end_timestamp = args.end

    request_body = {
        "params": {"start_timestamp": args.start, "end_timestamp": end_timestamp}
    }

    success = False
    attempts = 0

    while not success and attempts < args.max_retries:
        attempts += 1
        response = requests.post(
            request_url, json=request_body, headers=headers, timeout=10
        )
        response.raise_for_status()
        response_body = response.json()
        data_url = response_body["url"]

        keep_going = True
        num_retries = 0

        print(f"If-Modified-Since: {if_modified_since}")
        while keep_going:
            time.sleep(args.interval)
            num_retries += 1
            try:
                data_response = requests.get(
                    data_url,
                    headers={"If-Modified-Since": if_modified_since},
                    timeout=10,
                )
            except:
                print(f"Failed to get data from {data_url}", file=sys.stderr)
                continue
            print(f"Status code: {data_response.status_code}", file=sys.stderr)
            print(
                f"Last-Modified: {data_response.headers['Last-Modified']}",
                file=sys.stderr,
            )
            if data_response.status_code == 200:
                json.dump(data_response.json(), args.outfile)
                keep_going = False
                success = True
            if keep_going and args.max_retries > 0:
                keep_going = num_retries <= args.max_retries

    if not success:
        raise Exception("Failed to retrieve data")


def handle_sob(args: argparse.Namespace) -> None:
    milestone_2_cutoff = 29254405
    milestone_3_cutoff = 30192250

    token_metadata_index: Dict[str, Dict[str, Any]] = {}
    with open(args.merged, "r") as ifp:
        for line in ifp:
            item = json.loads(line.strip())
            token_metadata_index[str(item["token_id"])] = item

    with open(args.moonstream, "r") as ifp:
        full_data = json.load(ifp)

    with open(args.evolution, "r") as ifp:
        evolution_data = json.load(ifp)

    moonstream_data: List[Dict[str, Any]] = full_data["data"]

    moonstream_evolution_data: List[Dict[str, Any]] = evolution_data["data"]

    breeding_events: List[Dict[str, Any]] = []
    hatching_events: List[Dict[str, Any]] = []
    evolution_events: List[Dict[str, Any]] = []

    for event in moonstream_data:
        if event["event_type"] == "breeding":
            if event["block_number"] < milestone_2_cutoff:
                event["milestone_1"] = 50
                event["milestone_2"] = 0
                event["milestone_3"] = 0
            elif event["block_number"] < milestone_3_cutoff:
                event["milestone_1"] = 0
                event["milestone_2"] = 20
                event["milestone_3"] = 0
            else:
                event["milestone_1"] = 0
                event["milestone_2"] = 0
                event["milestone_3"] = 20

            event["is_hidden_class"] = 0
            metadata = token_metadata_index.get(event["token"])
            if metadata is not None and metadata["is_hidden_class"]:
                event["is_hidden_class"] = 1

                if event["block_number"] < milestone_2_cutoff:
                    event["milestone_1"] += 0
                    event["milestone_2"] += 0
                    event["milestone_3"] += 0
                elif event["block_number"] < milestone_3_cutoff:
                    event["milestone_1"] += 0
                    event["milestone_2"] += 0
                    event["milestone_3"] += 0
                else:
                    event["milestone_1"] += 0
                    event["milestone_2"] += 0
                    event["milestone_3"] += 30

            breeding_events.append(event)

        elif event["event_type"] == "hatchingEggs":
            event["milestone_1"] = 0
            event["milestone_2"] = 0
            event["milestone_3"] = 0

            metadata = token_metadata_index.get(event["token"])
            if metadata is not None and metadata["is_mythic"]:
                if event["block_number"] < milestone_2_cutoff:
                    event["milestone_1"] = 20
                    event["milestone_2"] = 0
                    event["milestone_3"] = 0
                elif event["block_number"] < milestone_3_cutoff:
                    event["milestone_1"] = 0
                    event["milestone_2"] = 20
                    event["milestone_3"] = 0
                else:
                    event["milestone_1"] = 0
                    event["milestone_2"] = 0
                    event["milestone_3"] = 20

            hatching_events.append(event)
        else:
            # Other conditions in this if statement in the future.
            pass

    for event in moonstream_evolution_data:
        if event["block_number"] < milestone_2_cutoff:
            event["milestone_1"] = 10
            event["milestone_2"] = 50
            event["milestone_3"] = 0
        elif event["block_number"] < milestone_3_cutoff:
            event["milestone_1"] = 0
            event["milestone_2"] = 50
            event["milestone_3"] = 0
        else:
            event["milestone_1"] = 0
            event["milestone_2"] = 0
            event["milestone_3"] = 10

        evolution_events.append(event)

    player_points: Dict[str, Dict[str, int]] = {}
    for event in breeding_events:
        player = event["player_wallet"]
        if player_points.get(player) is None:
            player_points[player] = {
                "milestone_1": 0,
                "milestone_2": 0,
                "milestone_3": 0,
                "total_score": 0,
                "num_breeds": 0,
                "num_hatches": 0,
                "num_mythic_hatches": 0,
                "num_evolutions": 0,
                "num_breeds_1": 0,
                "num_breeds_2": 0,
                "num_breeds_3": 0,
                "num_hatches_1": 0,
                "num_hatches_2": 0,
                "num_hatches_3": 0,
                "num_mythic_hatches_1": 0,
                "num_mythic_hatches_2": 0,
                "num_mythic_hatches_3": 0,
                "num_evolutions_1": 0,
                "num_evolutions_2": 0,
                "num_evolutions_3": 0,
                "num_hidden_class_3": 0,
                "block_number": event["block_number"],
            }
        player_points[player]["milestone_1"] += event["milestone_1"]
        player_points[player]["milestone_2"] += event["milestone_2"]
        player_points[player]["milestone_3"] += event["milestone_3"]
        player_points[player]["total_score"] += (
            event["milestone_1"] + event["milestone_2"] + event["milestone_3"]
        )

        player_points[player]["num_breeds"] += 1
        if event["block_number"] < milestone_2_cutoff:
            player_points[player]["num_breeds_1"] += 1
        elif event["block_number"] < milestone_3_cutoff:
            player_points[player]["num_breeds_2"] += 1
        else:
            player_points[player]["num_breeds_3"] += 1
            player_points[player]["num_hidden_class_3"] += event["is_hidden_class"]

    for event in hatching_events:
        player = event["player_wallet"]
        if player_points.get(player) is None:
            player_points[player] = {
                "milestone_1": 0,
                "milestone_2": 0,
                "milestone_3": 0,
                "total_score": 0,
                "num_breeds": 0,
                "num_hatches": 0,
                "num_mythic_hatches": 0,
                "num_evolutions": 0,
                "num_breeds_1": 0,
                "num_breeds_2": 0,
                "num_breeds_3": 0,
                "num_hatches_1": 0,
                "num_hatches_2": 0,
                "num_hatches_3": 0,
                "num_mythic_hatches_1": 0,
                "num_mythic_hatches_2": 0,
                "num_mythic_hatches_3": 0,
                "num_evolutions_1": 0,
                "num_evolutions_2": 0,
                "num_evolutions_3": 0,
                "num_hidden_class_3": 0,
                "block_number": event["block_number"],
            }
        player_points[player]["milestone_1"] += event["milestone_1"]
        player_points[player]["milestone_2"] += event["milestone_2"]
        player_points[player]["milestone_3"] += event["milestone_3"]
        player_points[player]["total_score"] += (
            event["milestone_1"] + event["milestone_2"] + event["milestone_3"]
        )
        player_points[player]["num_hatches"] += 1
        if event["block_number"] < milestone_2_cutoff:
            player_points[player]["num_hatches_1"] += 1
        elif event["block_number"] < milestone_3_cutoff:
            player_points[player]["num_hatches_2"] += 1
        else:
            player_points[player]["num_hatches_3"] += 1

        player_points[player]["num_mythic_hatches"] += int(
            event["milestone_1"] + event["milestone_2"] + event["milestone_3"] > 0
        )
        player_points[player]["num_mythic_hatches_1"] += int(event["milestone_1"] > 0)
        player_points[player]["num_mythic_hatches_2"] += int(event["milestone_2"] > 0)
        player_points[player]["num_mythic_hatches_3"] += int(event["milestone_3"] > 0)

    for event in evolution_events:
        player = event["player_wallet"]
        if player_points.get(player) is None:
            player_points[player] = {
                "milestone_1": 0,
                "milestone_2": 0,
                "milestone_3": 0,
                "total_score": 0,
                "num_breeds": 0,
                "num_hatches": 0,
                "num_mythic_hatches": 0,
                "num_evolutions": 0,
                "num_breeds_1": 0,
                "num_breeds_2": 0,
                "num_breeds_3": 0,
                "num_hatches_1": 0,
                "num_hatches_2": 0,
                "num_hatches_3": 0,
                "num_mythic_hatches_1": 0,
                "num_mythic_hatches_2": 0,
                "num_mythic_hatches_3": 0,
                "num_evolutions_1": 0,
                "num_evolutions_2": 0,
                "num_evolutions_3": 0,
                "num_hidden_class_3": 0,
                "block_number": event["block_number"],
            }

        player_points[player]["milestone_1"] += event["milestone_1"]
        player_points[player]["milestone_2"] += event["milestone_2"]
        player_points[player]["milestone_3"] += event["milestone_3"]
        player_points[player]["total_score"] += (
            event["milestone_2"] + event["milestone_3"]
        )

        player_points[player]["num_evolutions"] += 1
        if event["block_number"] < milestone_2_cutoff:
            player_points[player]["num_evolutions_1"] += 1
            player_points[player]["num_evolutions_2"] += 1
        elif event["block_number"] < milestone_3_cutoff:
            player_points[player]["num_evolutions_2"] += 1
        else:
            player_points[player]["num_evolutions_3"] += 1

    scores: List[Dict[str, Any]] = []
    for player, points in player_points.items():
        scores.append(
            {
                "address": player,
                "score": points["total_score"],
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

    metadata_parser.set_defaults(func=handle_metadata)

    mythic_body_parts_parser = subparsers.add_parser("mythic-body-parts")
    StatsFacet.add_default_arguments(mythic_body_parts_parser, False)
    mythic_body_parts_parser.add_argument(
        "--dnas",
        required=True,
        help='Path to JSON file containing results of "autocorns biologist dnas".',
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
        help="JSON file provided by Moonstream",
    )
    sob_parser.add_argument(
        "--evolution",
        required=True,
        help="JSON file provided by Moonstream",
    )

    sob_parser.set_defaults(func=handle_sob)

    moonstream_events_parser = subparsers.add_parser("moonstream-events")
    moonstream_events_parser.add_argument(
        "--api",
        default="https://api.moonstream.to",
        help="Moonstream API URL (default: https://api.moonstream.to). Access token expected to be set as MOONSTREAM_ACCESS_TOKEN environment variable.",
    )
    moonstream_events_parser.add_argument(
        "-n",
        "--query-name",
        required=True,
        help="Name of Moonstream Query API query to use to generate events data",
    )
    moonstream_events_parser.add_argument(
        "--start",
        required=True,
        type=int,
        help="Starting timestamp for data generation",
    )
    moonstream_events_parser.add_argument(
        "--end",
        type=int,
        required=False,
        help="Ending timestamp for data generation",
    )

    moonstream_events_parser.add_argument(
        "--interval", type=float, default=2.0, help="Polling interval for updated data"
    )
    moonstream_events_parser.add_argument(
        "--max-retries",
        type=int,
        default=0,
        help="Maximum number of retries for data (0 means unlimited).",
    )
    moonstream_events_parser.add_argument(
        "-o",
        "--outfile",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="(Optional) file to write output to. Default: sys.stdout",
    )

    moonstream_events_parser.set_defaults(func=handle_moonstream_events)

    total_supply_parser = subparsers.add_parser("total-supply")
    ERC721WithDiamondStorage.add_default_arguments(total_supply_parser, False)
    total_supply_parser.set_defaults(func=ERC721WithDiamondStorage.handle_total_supply)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
