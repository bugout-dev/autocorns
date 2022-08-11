import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple


from brownie import network, web3
from brownie.network import chain
from tqdm import tqdm

from . import DNAMigrationFacet

from . import Multicall2

from eth_typing.evm import ChecksumAddress


Multicall2_address_mumbay = "0xe9939e7Ea7D7fb619Ac57f648Da7B1D425832631"
Multicall2_address_mainnet = "0xc8E51042792d7405184DfCa245F2d27B94D013b6"


CALL_CHUNK_SIZE = 1000

def get_json_data(filename: str):
    x = open(filename, "r")
    y = json.loads(x.read())
    json_token_ids = []
    json_live_dna = []
    for i in y:
        json_token_ids.append(int(i["token_id"]))
        json_live_dna.append(i["live"])
    x.close()
    return json_token_ids, json_live_dna

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
    filename: str,
    block_number: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if block_number is None:
        block_number = len(chain) - 1
    
    token_ids, live_before = get_json_data(filename)

    contract = DNAMigrationFacet.DNAMigrationFacet(contract_address)

    results: List[Dict[str, Any]] = []

    errors: List[Dict[str, Any]] = []

    tokens_dnas = []

    dna_progress_bar = tqdm(
        total=len(token_ids),
        desc="Retrieving unicorn dnaReports",
    )

    CALL_CHUNK_SIZE_DNA = CALL_CHUNK_SIZE

    multicaller = Multicall2.Multicall2(Multicall2_address_mumbay)

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
                    contract.contract.dnaReport,
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

    for token_id, token_dna, live_dna_before in zip(token_ids, tokens_dnas, live_before):
        try:
            if token_dna[0] and token_dna[1] == token_dna[3] and token_dna[3] == live_dna_before:
                result = {
                    "token_id": token_id,
                    "block_number": block_number,
                    "predictive": token_dna[0],
                    "live": token_dna[1],
                    "canonical": token_dna[2],
                    "cached": token_dna[3],
                    "live dna before": live_dna_before,
                    "success": True
                }
                results.append(result)
            else:
                result = {
                    "token_id": token_id,
                    "block_number": block_number,
                    "predictive": token_dna[0],
                    "live": token_dna[1],
                    "canonical": token_dna[2],
                    "cached": token_dna[3],
                    "live dna before": live_dna_before,
                    "success": False
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


def handle_dnas(args: argparse.Namespace) -> None:
    network.connect(args.network)

    results, errors= unicorn_dnas(
        args.address,
        args.filename,
        args.block_number,
    )

    for result in results:
        print(json.dumps(result))

    for error in errors:
        print(json.dumps(error), file=sys.stderr)



def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crypto Unicorns genetics crawler")
    subparsers = parser.add_subparsers()

    dnas_parser = subparsers.add_parser("crawl", help="Crawl DNA report")
    DNAMigrationFacet.add_default_arguments(dnas_parser, False)
    dnas_parser.add_argument(
        "--filename",
        type=str,
        required=True,
        help="JSON Output Filename from previous crawler",
    )

    dnas_parser.set_defaults(func=handle_dnas)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
