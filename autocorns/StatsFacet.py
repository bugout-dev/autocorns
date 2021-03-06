# Code generated by moonworm : https://github.com/bugout-dev/moonworm
# Moonworm version : 0.2.2

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from brownie import Contract, network, project
from brownie.network.contract import ContractContainer
from eth_typing.evm import ChecksumAddress


PROJECT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
BUILD_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "build", "contracts")


def boolean_argument_type(raw_value: str) -> bool:
    TRUE_VALUES = ["1", "t", "y", "true", "yes"]
    FALSE_VALUES = ["0", "f", "n", "false", "no"]

    if raw_value.lower() in TRUE_VALUES:
        return True
    elif raw_value.lower() in FALSE_VALUES:
        return False

    raise ValueError(
        f"Invalid boolean argument: {raw_value}. Value must be one of: {','.join(TRUE_VALUES + FALSE_VALUES)}"
    )


def bytes_argument_type(raw_value: str) -> str:
    return raw_value


def get_abi_json(abi_name: str) -> List[Dict[str, Any]]:
    abi_full_path = os.path.join(BUILD_DIRECTORY, f"{abi_name}.json")
    if not os.path.isfile(abi_full_path):
        raise IOError(
            f"File does not exist: {abi_full_path}. Maybe you have to compile the smart contracts?"
        )

    with open(abi_full_path, "r") as ifp:
        build = json.load(ifp)

    abi_json = build.get("abi")
    if abi_json is None:
        raise ValueError(f"Could not find ABI definition in: {abi_full_path}")

    return abi_json


def contract_from_build(abi_name: str) -> ContractContainer:
    # This is workaround because brownie currently doesn't support loading the same project multiple
    # times. This causes problems when using multiple contracts from the same project in the same
    # python project.
    PROJECT = project.main.Project("moonworm", Path(PROJECT_DIRECTORY))

    abi_full_path = os.path.join(BUILD_DIRECTORY, f"{abi_name}.json")
    if not os.path.isfile(abi_full_path):
        raise IOError(
            f"File does not exist: {abi_full_path}. Maybe you have to compile the smart contracts?"
        )

    with open(abi_full_path, "r") as ifp:
        build = json.load(ifp)

    return ContractContainer(PROJECT, build)


class StatsFacet:
    def __init__(self, contract_address: Optional[ChecksumAddress]):
        self.contract_name = "StatsFacet"
        self.address = contract_address
        self.contract = None
        self.abi = get_abi_json("StatsFacet")
        if self.address is not None:
            self.contract: Optional[Contract] = Contract.from_abi(
                self.contract_name, self.address, self.abi
            )

    def deploy(self, transaction_config):
        contract_class = contract_from_build(self.contract_name)
        deployed_contract = contract_class.deploy(transaction_config)
        self.address = deployed_contract.address
        self.contract = deployed_contract
        return deployed_contract.tx

    def assert_contract_is_instantiated(self) -> None:
        if self.contract is None:
            raise Exception("contract has not been instantiated")

    def verify_contract(self):
        self.assert_contract_is_instantiated()
        contract_class = contract_from_build(self.contract_name)
        contract_class.publish_source(self.contract)

    def get_accuracy(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getAccuracy.call(_dna, block_identifier=block_number)

    def get_attack(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getAttack.call(_dna, block_identifier=block_number)

    def get_attack_speed(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getAttackSpeed.call(_dna, block_identifier=block_number)

    def get_defense(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getDefense.call(_dna, block_identifier=block_number)

    def get_endurance_score(
        self, token_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getEnduranceScore.call(
            token_id, block_identifier=block_number
        )

    def get_intelligence_score(
        self, token_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getIntelligenceScore.call(
            token_id, block_identifier=block_number
        )

    def get_magic(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getMagic.call(_dna, block_identifier=block_number)

    def get_movement_speed(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getMovementSpeed.call(_dna, block_identifier=block_number)

    def get_power_score(
        self, token_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getPowerScore.call(token_id, block_identifier=block_number)

    def get_resistance(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getResistance.call(_dna, block_identifier=block_number)

    def get_speed_score(
        self, token_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getSpeedScore.call(token_id, block_identifier=block_number)

    def get_stats(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getStats.call(_dna, block_identifier=block_number)

    def get_unicorn_body_parts(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getUnicornBodyParts.call(
            _dna, block_identifier=block_number
        )

    def get_unicorn_body_parts_local(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getUnicornBodyPartsLocal.call(
            _dna, block_identifier=block_number
        )

    def get_unicorn_metadata(
        self, _token_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getUnicornMetadata.call(
            _token_id, block_identifier=block_number
        )

    def get_vitality(
        self, _dna: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getVitality.call(_dna, block_identifier=block_number)


def get_transaction_config(args: argparse.Namespace) -> Dict[str, Any]:
    signer = network.accounts.load(args.sender, args.password)
    transaction_config: Dict[str, Any] = {"from": signer}
    if args.gas_price is not None:
        transaction_config["gas_price"] = args.gas_price
    if args.max_fee_per_gas is not None:
        transaction_config["max_fee"] = args.max_fee_per_gas
    if args.max_priority_fee_per_gas is not None:
        transaction_config["priority_fee"] = args.max_priority_fee_per_gas
    if args.confirmations is not None:
        transaction_config["required_confs"] = args.confirmations
    if args.nonce is not None:
        transaction_config["nonce"] = args.nonce
    return transaction_config


def add_default_arguments(parser: argparse.ArgumentParser, transact: bool) -> None:
    parser.add_argument(
        "--network", required=True, help="Name of brownie network to connect to"
    )
    parser.add_argument(
        "--address", required=False, help="Address of deployed contract to connect to"
    )
    if not transact:
        parser.add_argument(
            "--block-number",
            required=False,
            type=int,
            help="Call at the given block number, defaults to latest",
        )
        return
    parser.add_argument(
        "--sender", required=True, help="Path to keystore file for transaction sender"
    )
    parser.add_argument(
        "--password",
        required=False,
        help="Password to keystore file (if you do not provide it, you will be prompted for it)",
    )
    parser.add_argument(
        "--gas-price", default=None, help="Gas price at which to submit transaction"
    )
    parser.add_argument(
        "--max-fee-per-gas",
        default=None,
        help="Max fee per gas for EIP1559 transactions",
    )
    parser.add_argument(
        "--max-priority-fee-per-gas",
        default=None,
        help="Max priority fee per gas for EIP1559 transactions",
    )
    parser.add_argument(
        "--confirmations",
        type=int,
        default=None,
        help="Number of confirmations to await before considering a transaction completed",
    )
    parser.add_argument(
        "--nonce", type=int, default=None, help="Nonce for the transaction (optional)"
    )
    parser.add_argument(
        "--value", default=None, help="Value of the transaction in wei(optional)"
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")


def handle_deploy(args: argparse.Namespace) -> None:
    network.connect(args.network)
    transaction_config = get_transaction_config(args)
    contract = StatsFacet(None)
    result = contract.deploy(transaction_config=transaction_config)
    print(result)
    print(result.info())


def handle_verify_contract(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.verify_contract()
    print(result)


def handle_get_accuracy(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_accuracy(_dna=args.dna_arg, block_number=args.block_number)
    print(result)


def handle_get_attack(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_attack(_dna=args.dna_arg, block_number=args.block_number)
    print(result)


def handle_get_attack_speed(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_attack_speed(
        _dna=args.dna_arg, block_number=args.block_number
    )
    print(result)


def handle_get_defense(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_defense(_dna=args.dna_arg, block_number=args.block_number)
    print(result)


def handle_get_endurance_score(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_endurance_score(
        token_id=args.token_id, block_number=args.block_number
    )
    print(result)


def handle_get_intelligence_score(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_intelligence_score(
        token_id=args.token_id, block_number=args.block_number
    )
    print(result)


def handle_get_magic(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_magic(_dna=args.dna_arg, block_number=args.block_number)
    print(result)


def handle_get_movement_speed(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_movement_speed(
        _dna=args.dna_arg, block_number=args.block_number
    )
    print(result)


def handle_get_power_score(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_power_score(
        token_id=args.token_id, block_number=args.block_number
    )
    print(result)


def handle_get_resistance(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_resistance(_dna=args.dna_arg, block_number=args.block_number)
    print(result)


def handle_get_speed_score(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_speed_score(
        token_id=args.token_id, block_number=args.block_number
    )
    print(result)


def handle_get_stats(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_stats(_dna=args.dna_arg, block_number=args.block_number)
    print(result)


def handle_get_unicorn_body_parts(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_unicorn_body_parts(
        _dna=args.dna_arg, block_number=args.block_number
    )
    print(result)


def handle_get_unicorn_body_parts_local(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_unicorn_body_parts_local(
        _dna=args.dna_arg, block_number=args.block_number
    )
    print(result)


def handle_get_unicorn_metadata(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_unicorn_metadata(
        _token_id=args.token_id_arg, block_number=args.block_number
    )
    print(result)


def handle_get_vitality(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = StatsFacet(args.address)
    result = contract.get_vitality(_dna=args.dna_arg, block_number=args.block_number)
    print(result)


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI for StatsFacet")
    parser.set_defaults(func=lambda _: parser.print_help())
    subcommands = parser.add_subparsers()

    deploy_parser = subcommands.add_parser("deploy")
    add_default_arguments(deploy_parser, True)
    deploy_parser.set_defaults(func=handle_deploy)

    verify_contract_parser = subcommands.add_parser("verify-contract")
    add_default_arguments(verify_contract_parser, False)
    verify_contract_parser.set_defaults(func=handle_verify_contract)

    get_accuracy_parser = subcommands.add_parser("get-accuracy")
    add_default_arguments(get_accuracy_parser, False)
    get_accuracy_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_accuracy_parser.set_defaults(func=handle_get_accuracy)

    get_attack_parser = subcommands.add_parser("get-attack")
    add_default_arguments(get_attack_parser, False)
    get_attack_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_attack_parser.set_defaults(func=handle_get_attack)

    get_attack_speed_parser = subcommands.add_parser("get-attack-speed")
    add_default_arguments(get_attack_speed_parser, False)
    get_attack_speed_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_attack_speed_parser.set_defaults(func=handle_get_attack_speed)

    get_defense_parser = subcommands.add_parser("get-defense")
    add_default_arguments(get_defense_parser, False)
    get_defense_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_defense_parser.set_defaults(func=handle_get_defense)

    get_endurance_score_parser = subcommands.add_parser("get-endurance-score")
    add_default_arguments(get_endurance_score_parser, False)
    get_endurance_score_parser.add_argument(
        "--token-id", required=True, help="Type: uint256", type=int
    )
    get_endurance_score_parser.set_defaults(func=handle_get_endurance_score)

    get_intelligence_score_parser = subcommands.add_parser("get-intelligence-score")
    add_default_arguments(get_intelligence_score_parser, False)
    get_intelligence_score_parser.add_argument(
        "--token-id", required=True, help="Type: uint256", type=int
    )
    get_intelligence_score_parser.set_defaults(func=handle_get_intelligence_score)

    get_magic_parser = subcommands.add_parser("get-magic")
    add_default_arguments(get_magic_parser, False)
    get_magic_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_magic_parser.set_defaults(func=handle_get_magic)

    get_movement_speed_parser = subcommands.add_parser("get-movement-speed")
    add_default_arguments(get_movement_speed_parser, False)
    get_movement_speed_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_movement_speed_parser.set_defaults(func=handle_get_movement_speed)

    get_power_score_parser = subcommands.add_parser("get-power-score")
    add_default_arguments(get_power_score_parser, False)
    get_power_score_parser.add_argument(
        "--token-id", required=True, help="Type: uint256", type=int
    )
    get_power_score_parser.set_defaults(func=handle_get_power_score)

    get_resistance_parser = subcommands.add_parser("get-resistance")
    add_default_arguments(get_resistance_parser, False)
    get_resistance_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_resistance_parser.set_defaults(func=handle_get_resistance)

    get_speed_score_parser = subcommands.add_parser("get-speed-score")
    add_default_arguments(get_speed_score_parser, False)
    get_speed_score_parser.add_argument(
        "--token-id", required=True, help="Type: uint256", type=int
    )
    get_speed_score_parser.set_defaults(func=handle_get_speed_score)

    get_stats_parser = subcommands.add_parser("get-stats")
    add_default_arguments(get_stats_parser, False)
    get_stats_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_stats_parser.set_defaults(func=handle_get_stats)

    get_unicorn_body_parts_parser = subcommands.add_parser("get-unicorn-body-parts")
    add_default_arguments(get_unicorn_body_parts_parser, False)
    get_unicorn_body_parts_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_unicorn_body_parts_parser.set_defaults(func=handle_get_unicorn_body_parts)

    get_unicorn_body_parts_local_parser = subcommands.add_parser(
        "get-unicorn-body-parts-local"
    )
    add_default_arguments(get_unicorn_body_parts_local_parser, False)
    get_unicorn_body_parts_local_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_unicorn_body_parts_local_parser.set_defaults(
        func=handle_get_unicorn_body_parts_local
    )

    get_unicorn_metadata_parser = subcommands.add_parser("get-unicorn-metadata")
    add_default_arguments(get_unicorn_metadata_parser, False)
    get_unicorn_metadata_parser.add_argument(
        "--token-id-arg", required=True, help="Type: uint256", type=int
    )
    get_unicorn_metadata_parser.set_defaults(func=handle_get_unicorn_metadata)

    get_vitality_parser = subcommands.add_parser("get-vitality")
    add_default_arguments(get_vitality_parser, False)
    get_vitality_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    get_vitality_parser.set_defaults(func=handle_get_vitality)

    return parser


def main() -> None:
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
