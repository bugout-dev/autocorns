import argparse
import csv
import datetime
import json
import os
import random
import sys
import time
from typing import Any, cast, Dict, List, Optional, Set, Tuple


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
# BLOCK_STALENESS_THRESHOLD estimated using a Polygon block interval of 2.3 seconds per block to get
# us close to 24 hours of freshness in a checkpoint:
# (3600/2.3)*24 is 37565.2173913.
BLOCK_STALENESS_THRESHOLD = 37565


Multicall2_address = "0xc8E51042792d7405184DfCa245F2d27B94D013b6"


def load_checkpoint_data(checkpoint_file: Optional[str]) -> List[Dict[str, Any]]:
    checkpoint_data: List[Dict[str, Any]] = []
    if checkpoint_file is None or not os.path.exists(checkpoint_file):
        return []

    with open(checkpoint_file, "r") as ifp:
        for line in ifp:
            stripped_line = line.strip()
            if stripped_line:
                item = cast(Dict[str, Any], json.loads(stripped_line))
                checkpoint_data.append(item)
    return checkpoint_data


def expire_stale_checkpoint_data(
    checkpoint_data: List[Dict[str, Any]], min_block_number: int
) -> List[Dict[str, Any]]:
    return [
        item
        for item in checkpoint_data
        if item.get("block_number", 0) >= min_block_number
    ]


def leak_checkpoint_data(
    checkpoint_data: List[Dict[str, Any]],
    leak_rate: float,
) -> List[Dict[str, Any]]:
    assert 0 <= leak_rate <= 1, "Leak rate must be between 0 and 1"
    return [item for item in checkpoint_data if random.random() > leak_rate]


def apply_checkpoint(
    job_list: List[Any],
    checkpoint_data: List[Dict[str, Any]],
    checkpoint_key: str,
    job_list_key: Optional[str] = None,
) -> List[Any]:
    checkpointed_jobs = {item.get(checkpoint_key) for item in checkpoint_data}
    if job_list_key is None:
        uncheckpointed_jobs = [job for job in job_list if job not in checkpointed_jobs]
    else:
        uncheckpointed_jobs = [
            job for job in job_list if job[job_list_key] not in checkpointed_jobs
        ]
    return uncheckpointed_jobs


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
        desc="Submitting requests for unicorn on-chain metadata",
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


def unicorn_stats(
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
        desc="Retrieving unicorn stats",
    )

    contract = StatsFacet.StatsFacet(contract_address)

    block_number = dnas[0]["block_number"]

    multicaller = Multicall2.Multicall2(Multicall2_address)

    multicall_method = multicaller.contract.tryAggregate

    dnas_is_present = [
        dna for dna in dnas if dna["dna"] is not None and dna["dna"] != "None"
    ]

    CALL_CHUNK_SIZE_STATS = int(CALL_CHUNK_SIZE / 6)
    for dnas_chunk in [
        dnas_is_present[i : i + CALL_CHUNK_SIZE_STATS]
        for i in range(0, len(dnas), CALL_CHUNK_SIZE_STATS)
    ]:
        while True:
            try:

                send_to_multicall_dnas = [dna["dna"] for dna in dnas_chunk]

                make_multicall_result = make_multicall(
                    multicall_method,
                    contract.contract.getStats,
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

    stats_order = [
        "attack",
        "accuracy",
        "movement_speed",
        "attack_speed",
        "defense",
        "vitality",
        "resistance",
        "magic",
    ]

    for item, token_data in zip(dnas_is_present, tokens_metadata):
        if token_data is None:
            errors.append(f"No DNA for token ID: {item['token_id']}")
            # Token item['token_id']} has no DNA
            continue
        stats_data = {
            stat_name: stat_value
            for stat_name, stat_value in zip(stats_order, token_data)
        }
        try:
            result = {**item, **stats_data, "sum_stats": sum(token_data)}
            results.append(result)
        except:
            errors.append(f"Could not process stats for token ID: {item['token_id']}")

    return results, errors


def handle_dnas(args: argparse.Namespace) -> None:
    network.connect(args.network)
    final_checkpoint_data = []
    if args.checkpoint:
        block_number = len(chain)
        checkpoint_data = load_checkpoint_data(args.checkpoint)
        fresh_checkpoint_data = expire_stale_checkpoint_data(
            checkpoint_data, block_number - BLOCK_STALENESS_THRESHOLD
        )
        final_checkpoint_data = fresh_checkpoint_data
        if args.leak_rate is not None:
            final_checkpoint_data = leak_checkpoint_data(
                fresh_checkpoint_data, args.leak_rate
            )
    if args.end is None:
        args.end = args.start
    assert args.start <= args.end, "Starting token ID must not exceed ending token ID"
    all_token_ids = range(args.start, args.end + 1)
    token_ids = apply_checkpoint(all_token_ids, final_checkpoint_data, "token_id")
    results, errors = unicorn_dnas(
        args.address,
        token_ids,
        args.block_number,
    )

    if args.checkpoint:
        with open(args.checkpoint, "w") as ofp:
            for result in results + final_checkpoint_data:
                print(json.dumps(result), file=ofp)
    else:
        for result in results:
            print(json.dumps(result))

    for error in errors:
        print(json.dumps(error), file=sys.stderr)


def handle_metadata(args: argparse.Namespace) -> None:
    network.connect(args.network)
    final_checkpoint_data = []
    if args.checkpoint:
        block_number = len(chain)
        checkpoint_data = load_checkpoint_data(args.checkpoint)
        fresh_checkpoint_data = expire_stale_checkpoint_data(
            checkpoint_data, block_number - BLOCK_STALENESS_THRESHOLD
        )
        final_checkpoint_data = fresh_checkpoint_data
        if args.leak_rate is not None:
            final_checkpoint_data = leak_checkpoint_data(
                fresh_checkpoint_data, args.leak_rate
            )

    if args.end is None:
        args.end = args.start
    assert args.start <= args.end, "Starting token ID must not exceed ending token ID"
    all_token_ids = range(args.start, args.end + 1)
    token_ids = apply_checkpoint(all_token_ids, final_checkpoint_data, "token_id")
    results, errors = unicorn_metadata(
        args.address,
        token_ids,
        args.block_number,
    )

    if args.checkpoint:
        with open(args.checkpoint, "w") as ofp:
            for result in results + final_checkpoint_data:
                print(json.dumps(result), file=ofp)
    else:
        for result in results:
            print(json.dumps(result))

    for error in errors:
        print(json.dumps(error), file=sys.stderr)


def handle_mythic_body_parts(args: argparse.Namespace) -> None:
    network.connect(args.network)
    final_checkpoint_data = []
    if args.checkpoint:
        block_number = len(chain)
        checkpoint_data = load_checkpoint_data(args.checkpoint)
        fresh_checkpoint_data = expire_stale_checkpoint_data(
            checkpoint_data, block_number - BLOCK_STALENESS_THRESHOLD
        )
        final_checkpoint_data = fresh_checkpoint_data
        if args.leak_rate is not None:
            final_checkpoint_data = leak_checkpoint_data(
                fresh_checkpoint_data, args.leak_rate
            )

    all_dnas: List[Dict[str, Any]] = []
    with open(args.dnas, "r") as ifp:
        for line in ifp:
            all_dnas.append(json.loads(line.strip()))

    dnas = apply_checkpoint(all_dnas, final_checkpoint_data, "token_id", "token_id")

    results, errors = unicorn_mythic_body_parts(
        args.address,
        dnas,
        args.block_number,
    )

    if args.checkpoint:
        with open(args.checkpoint, "w") as ofp:
            for result in results + final_checkpoint_data:
                print(json.dumps(result), file=ofp)
    else:
        for result in results:
            print(json.dumps(result))

    for error in errors:
        json.dump(error, fp=sys.stderr)
        print("", file=sys.stderr)


def handle_stats(args: argparse.Namespace) -> None:
    network.connect(args.network)
    final_checkpoint_data = []
    if args.checkpoint:
        block_number = len(chain)
        checkpoint_data = load_checkpoint_data(args.checkpoint)
        fresh_checkpoint_data = expire_stale_checkpoint_data(
            checkpoint_data, block_number - BLOCK_STALENESS_THRESHOLD
        )
        final_checkpoint_data = fresh_checkpoint_data
        if args.leak_rate is not None:
            final_checkpoint_data = leak_checkpoint_data(
                fresh_checkpoint_data, args.leak_rate
            )

    all_dnas: List[Dict[str, Any]] = []
    with open(args.dnas, "r") as ifp:
        for line in ifp:
            all_dnas.append(json.loads(line.strip()))

    dnas = apply_checkpoint(all_dnas, final_checkpoint_data, "token_id", "token_id")

    results, errors = unicorn_stats(
        args.address,
        dnas,
        args.block_number,
    )

    if args.checkpoint:
        with open(args.checkpoint, "w") as ofp:
            for result in results + final_checkpoint_data:
                print(json.dumps(result), file=ofp)
    else:
        for result in results:
            print(json.dumps(result))

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
            lifecycle_stage = data["lifecycle_stage"]
            result["mythic_body_parts_block_number"] = mythic_body_parts_data[
                "block_number"
            ]
            if (
                mythic_body_parts_data.get("num_mythic_body_parts") is None
                and result["lifecycle_stage"] == 0
            ):
                result["num_mythic_body_parts"] = 0
            if (
                mythic_body_parts_data.get("num_mythic_body_parts") == 6
                and lifecycle_stage == 0
            ):
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
    time.sleep(4)
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
    milestone_3_end = 31372175

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
            elif event["block_number"] <= milestone_3_end:
                event["milestone_1"] = 0
                event["milestone_2"] = 0
                event["milestone_3"] = 20
            else:
                event["milestone_1"] = 0
                event["milestone_2"] = 0
                event["milestone_3"] = 0

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
                elif event["block_number"] <= milestone_3_end:
                    event["milestone_1"] += 0
                    event["milestone_2"] += 0
                    event["milestone_3"] += 30
                else:
                    event["milestone_1"] += 0
                    event["milestone_2"] += 0
                    event["milestone_3"] += 0

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
                elif event["block_number"] <= milestone_3_end:
                    event["milestone_1"] = 0
                    event["milestone_2"] = 0
                    event["milestone_3"] = 20
                else:
                    event["milestone_1"] = 0
                    event["milestone_2"] = 0
                    event["milestone_3"] = 0

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
        elif event["block_number"] <= milestone_3_end:
            event["milestone_1"] = 0
            event["milestone_2"] = 0
            event["milestone_3"] = 10
        else:
            event["milestone_1"] = 0
            event["milestone_2"] = 0
            event["milestone_3"] = 0

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
        elif event["block_number"] <= milestone_3_end:
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
        elif event["block_number"] <= milestone_3_end:
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
        elif event["block_number"] <= milestone_3_end:
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


def handle_fall_event_2022(args: argparse.Namespace) -> None:
    mythic_body_parts_index: Dict[str, Dict[str, Any]] = {}
    with open(args.mythic_body_parts, "r") as ifp:
        for line in ifp:
            item = json.loads(line.strip())
            mythic_body_parts_index[str(item["token_id"])] = item

    stats_index: Dict[str, Dict[str, Any]] = {}
    with open(args.stats, "r") as ifp:
        for line in ifp:
            item = json.loads(line.strip())
            stats_index[str(item["token_id"])] = item

    metadata_index: Dict[str, Dict[str, Any]] = {}
    with open(args.metadata, "r") as ifp:
        for line in ifp:
            item = json.loads(line.strip())
            metadata_index[str(item["token_id"])] = item

    with open(args.breeding_hatching_events, "r") as ifp:
        breeding_hatching_data = json.load(ifp)

    with open(args.evolution_events, "r") as ifp:
        evolution_data = json.load(ifp)

    moonstream_breeding_hatching_data: List[Dict[str, Any]] = breeding_hatching_data[
        "data"
    ]

    breeding_events: List[Dict[str, Any]] = [
        event
        for event in moonstream_breeding_hatching_data
        if event["event_type"] == "breeding"
    ]
    hatching_events: List[Dict[str, Any]] = [
        event
        for event in moonstream_breeding_hatching_data
        if event["event_type"] == "hatchingEggs"
    ]
    evolution_events: List[Dict[str, Any]] = evolution_data["data"]

    default_player_points = {
        "num_bred": 0,
        "num_evolved": 0,
        "num_evolved_with_at_least_1300_stat_points": 0,
        "num_mythic_body_parts_hatched": 0,
    }

    player_points: Dict[str, Dict[str, int]] = {}
    for event in breeding_events:
        player = event["player_wallet"]
        if player_points.get(player) is None:
            player_points[player] = {**default_player_points}

        player_points[player]["num_bred"] += 1

    for event in hatching_events:
        player = event["player_wallet"]
        if player_points.get(player) is None:
            player_points[player] = {**default_player_points}

        token_id = str(event["token"])
        mythic_body_parts_info = mythic_body_parts_index[token_id]
        if metadata_index.get(token_id) is not None:
            if (
                metadata_index[token_id].get("lifecycle_stage") is not None
                and metadata_index[token_id]["lifecycle_stage"] != 0
            ):
                player_points[player][
                    "num_mythic_body_parts_hatched"
                ] += mythic_body_parts_info["num_mythic_body_parts"]

    for event in evolution_events:
        player = event["player_wallet"]
        if player_points.get(player) is None:
            player_points[player] = {**default_player_points}

        player_points[player]["num_evolved"] += 1
        token_id = str(event["token"])
        sum_stats = stats_index.get(token_id, {}).get("sum_stats", 0)
        if sum_stats >= 1300:
            player_points[player]["num_evolved_with_at_least_1300_stat_points"] += 1

    scores: List[Dict[str, Any]] = []
    for player, points in player_points.items():
        total_score = (
            (100 * points["num_evolved_with_at_least_1300_stat_points"])
            + (50 * points["num_mythic_body_parts_hatched"])
            + (25 * points["num_evolved"])
            + (10 * points["num_bred"])
        )
        scores.append(
            {
                "address": player,
                "score": total_score,
                "points_data": points,
            }
        )

    scores.sort(key=lambda item: item["score"], reverse=True)

    print(json.dumps(scores))


def handle_leaderboard_to_csv(args: argparse.Namespace) -> None:
    """
    Converts leaderboard JSON file into CSV.
    """
    with open(args.infile, "r") as ifp:
        leaderboard = json.load(ifp)

    if len(leaderboard) == 0:
        raise ValueError("Empty leaderboard")

    points_data_columns = [key for key in leaderboard[0]["points_data"]]
    header = ["address", "score"] + points_data_columns
    writer = csv.writer(sys.stdout)
    try:
        writer.writerow(header)
        csv_rows = [
            [row["address"], row["score"]]
            + [row["points_data"].get(key, 0) for key in points_data_columns]
            for row in leaderboard
        ]
        writer.writerows(csv_rows)
    except BrokenPipeError:
        sys.exit(0)


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
        "--checkpoint", default=None, help="Checkpoint file (optional)"
    )
    dnas_parser.add_argument(
        "--leak-rate",
        type=float,
        required=False,
        default=None,
        help="Rate at which data should leak out of checkpoint",
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
        "--checkpoint", default=None, help="Checkpoint file (optional)"
    )
    metadata_parser.add_argument(
        "--leak-rate",
        type=float,
        required=False,
        default=None,
        help="Rate at which data should leak out of checkpoint",
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
        "--checkpoint", default=None, help="Checkpoint file (optional)"
    )
    mythic_body_parts_parser.add_argument(
        "--leak-rate",
        type=float,
        required=False,
        default=None,
        help="Rate at which data should leak out of checkpoint",
    )

    mythic_body_parts_parser.set_defaults(func=handle_mythic_body_parts)

    stats_parser = subparsers.add_parser("stats")
    StatsFacet.add_default_arguments(stats_parser, False)
    stats_parser.add_argument(
        "--dnas",
        required=True,
        help='Path to JSON file containing results of "autocorns biologist dnas".',
    )
    stats_parser.add_argument(
        "--checkpoint", default=None, help="Checkpoint file (optional)"
    )
    stats_parser.add_argument(
        "--leak-rate",
        type=float,
        required=False,
        default=None,
        help="Rate at which data should leak out of checkpoint",
    )

    stats_parser.set_defaults(func=handle_stats)

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

    fall_event_2022_parser = subparsers.add_parser("fall-event-2022")
    fall_event_2022_parser.add_argument(
        "--mythic-body-parts",
        required=True,
        help="Checkpoint file for mythic body parts",
    )
    fall_event_2022_parser.add_argument(
        "--stats", required=True, help="Checkpoint file for Unicorn stats"
    )
    fall_event_2022_parser.add_argument(
        "--metadata",
        required=True,
        help="Checkpoint file for Unicorn metadata",
    )
    fall_event_2022_parser.add_argument(
        "--breeding-hatching-events",
        required=True,
        help="JSON file containing the results of the breeding_hatching_events Moonstream Query",
    )
    fall_event_2022_parser.add_argument(
        "--evolution-events",
        required=True,
        help="JSON file containing the results of the evolution_events Moonstream Query",
    )

    fall_event_2022_parser.set_defaults(func=handle_fall_event_2022)

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

    leaderboard_to_csv_parser = subparsers.add_parser(
        "leaderboard-to-csv",
        description="Converts a leaderboard.json file (as produced by the sob command) into a CSV file. Output is written to stdout.",
    )
    leaderboard_to_csv_parser.add_argument(
        "infile",
        help="Path to leaderboard.json file, or a file in the same format as that one",
    )
    leaderboard_to_csv_parser.set_defaults(func=handle_leaderboard_to_csv)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
