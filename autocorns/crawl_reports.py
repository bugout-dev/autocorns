import argparse
import json
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

    for token_id, token_dna in zip(token_ids, tokens_dnas):
        try:
            if not token_dna[0]:
                continue
            result = {
                "token_id": token_id,
                "block_number": block_number,
                "dnaReport": token_dna,
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


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crypto Unicorns genetics crawler")
    subparsers = parser.add_subparsers()

    dnas_parser = subparsers.add_parser("dna-report", help="Generate DNA report")
    DNAMigrationFacet.add_default_arguments(dnas_parser, False)
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

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
