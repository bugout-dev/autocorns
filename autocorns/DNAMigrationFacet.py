# Code generated by moonworm : https://github.com/bugout-dev/moonworm
# Moonworm version : 0.2.4

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


class DNAMigrationFacet:
    def __init__(self, contract_address: Optional[ChecksumAddress]):
        self.contract_name = "DNAMigrationFacet"
        self.address = contract_address
        self.contract = None
        self.abi = get_abi_json("DNAMigrationFacet")
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

    def admin_correct_birthday(
        self, _token_id: int, _birthday: int, transaction_config
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.adminCorrectBirthday(
            _token_id, _birthday, transaction_config
        )

    def admin_correct_dna(self, _token_id: int, _dna: int, transaction_config) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.adminCorrectDNA(_token_id, _dna, transaction_config)

    def cache_volatile_hatch_dna(self, _token_ids: List, transaction_config) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.cacheVolatileHatchDNA(_token_ids, transaction_config)

    def dna_report(
        self, _token_id: int, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.dnaReport.call(_token_id, block_identifier=block_number)

    def get_target_dna_version(
        self, block_number: Optional[Union[str, int]] = "latest"
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.getTargetDNAVersion.call(block_identifier=block_number)

    def migrate_unicorns_to_v2_dna(
        self,
        _token_ids: List,
        _first_names: List,
        _last_names: List,
        _bypass_dna_events: bool,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.migrateUnicornsToV2DNA(
            _token_ids,
            _first_names,
            _last_names,
            _bypass_dna_events,
            transaction_config,
        )

    def migrate_unicorns_to_v2_dna_by_id_range(
        self,
        _first_token_id: int,
        _last_token_id: int,
        _first_names: List,
        _last_names: List,
        _bypass_dna_events: bool,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.migrateUnicornsToV2DNAByIDRange(
            _first_token_id,
            _last_token_id,
            _first_names,
            _last_names,
            _bypass_dna_events,
            transaction_config,
        )

    def rollback_v2_dna_to_v1_dna(
        self,
        _token_ids: List,
        _bypass_dna_events: bool,
        _force: bool,
        transaction_config,
    ) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.rollbackV2DNAToV1DNA(
            _token_ids, _bypass_dna_events, _force, transaction_config
        )

    def set_target_dna_version(self, _version_number: int, transaction_config) -> Any:
        self.assert_contract_is_instantiated()
        return self.contract.setTargetDNAVersion(_version_number, transaction_config)


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
    contract = DNAMigrationFacet(None)
    result = contract.deploy(transaction_config=transaction_config)
    print(result)
    if args.verbose:
        print(result.info())


def handle_verify_contract(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    result = contract.verify_contract()
    print(result)


def handle_admin_correct_birthday(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.admin_correct_birthday(
        _token_id=args.token_id_arg,
        _birthday=args.birthday_arg,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_admin_correct_dna(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.admin_correct_dna(
        _token_id=args.token_id_arg,
        _dna=args.dna_arg,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_cache_volatile_hatch_dna(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.cache_volatile_hatch_dna(
        _token_ids=args.token_ids_arg, transaction_config=transaction_config
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_dna_report(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    result = contract.dna_report(
        _token_id=args.token_id_arg, block_number=args.block_number
    )
    print(result)


def handle_get_target_dna_version(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    result = contract.get_target_dna_version(block_number=args.block_number)
    print(result)


def handle_migrate_unicorns_to_v2_dna(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.migrate_unicorns_to_v2_dna(
        _token_ids=args.token_ids_arg,
        _first_names=args.first_names_arg,
        _last_names=args.last_names_arg,
        _bypass_dna_events=args.bypass_dna_events_arg,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_migrate_unicorns_to_v2_dna_by_id_range(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.migrate_unicorns_to_v2_dna_by_id_range(
        _first_token_id=args.first_token_id_arg,
        _last_token_id=args.last_token_id_arg,
        _first_names=args.first_names_arg,
        _last_names=args.last_names_arg,
        _bypass_dna_events=args.bypass_dna_events_arg,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_rollback_v2_dna_to_v1_dna(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.rollback_v2_dna_to_v1_dna(
        _token_ids=args.token_ids_arg,
        _bypass_dna_events=args.bypass_dna_events_arg,
        _force=args.force_arg,
        transaction_config=transaction_config,
    )
    print(result)
    if args.verbose:
        print(result.info())


def handle_set_target_dna_version(args: argparse.Namespace) -> None:
    network.connect(args.network)
    contract = DNAMigrationFacet(args.address)
    transaction_config = get_transaction_config(args)
    result = contract.set_target_dna_version(
        _version_number=args.version_number_arg, transaction_config=transaction_config
    )
    print(result)
    if args.verbose:
        print(result.info())


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI for DNAMigrationFacet")
    parser.set_defaults(func=lambda _: parser.print_help())
    subcommands = parser.add_subparsers()

    deploy_parser = subcommands.add_parser("deploy")
    add_default_arguments(deploy_parser, True)
    deploy_parser.set_defaults(func=handle_deploy)

    verify_contract_parser = subcommands.add_parser("verify-contract")
    add_default_arguments(verify_contract_parser, False)
    verify_contract_parser.set_defaults(func=handle_verify_contract)

    admin_correct_birthday_parser = subcommands.add_parser("admin-correct-birthday")
    add_default_arguments(admin_correct_birthday_parser, True)
    admin_correct_birthday_parser.add_argument(
        "--token-id-arg", required=True, help="Type: uint256", type=int
    )
    admin_correct_birthday_parser.add_argument(
        "--birthday-arg", required=True, help="Type: uint256", type=int
    )
    admin_correct_birthday_parser.set_defaults(func=handle_admin_correct_birthday)

    admin_correct_dna_parser = subcommands.add_parser("admin-correct-dna")
    add_default_arguments(admin_correct_dna_parser, True)
    admin_correct_dna_parser.add_argument(
        "--token-id-arg", required=True, help="Type: uint256", type=int
    )
    admin_correct_dna_parser.add_argument(
        "--dna-arg", required=True, help="Type: uint256", type=int
    )
    admin_correct_dna_parser.set_defaults(func=handle_admin_correct_dna)

    cache_volatile_hatch_dna_parser = subcommands.add_parser("cache-volatile-hatch-dna")
    add_default_arguments(cache_volatile_hatch_dna_parser, True)
    cache_volatile_hatch_dna_parser.add_argument(
        "--token-ids-arg", required=True, help="Type: uint256[]", nargs="+"
    )
    cache_volatile_hatch_dna_parser.set_defaults(func=handle_cache_volatile_hatch_dna)

    dna_report_parser = subcommands.add_parser("dna-report")
    add_default_arguments(dna_report_parser, False)
    dna_report_parser.add_argument(
        "--token-id-arg", required=True, help="Type: uint256", type=int
    )
    dna_report_parser.set_defaults(func=handle_dna_report)

    get_target_dna_version_parser = subcommands.add_parser("get-target-dna-version")
    add_default_arguments(get_target_dna_version_parser, False)
    get_target_dna_version_parser.set_defaults(func=handle_get_target_dna_version)

    migrate_unicorns_to_v2_dna_parser = subcommands.add_parser(
        "migrate-unicorns-to-v2-dna"
    )
    add_default_arguments(migrate_unicorns_to_v2_dna_parser, True)
    migrate_unicorns_to_v2_dna_parser.add_argument(
        "--token-ids-arg", required=True, help="Type: uint256[]", nargs="+"
    )
    migrate_unicorns_to_v2_dna_parser.add_argument(
        "--first-names-arg", required=True, help="Type: uint16[]", nargs="+"
    )
    migrate_unicorns_to_v2_dna_parser.add_argument(
        "--last-names-arg", required=True, help="Type: uint16[]", nargs="+"
    )
    migrate_unicorns_to_v2_dna_parser.add_argument(
        "--bypass-dna-events-arg",
        required=True,
        help="Type: bool",
        type=boolean_argument_type,
    )
    migrate_unicorns_to_v2_dna_parser.set_defaults(
        func=handle_migrate_unicorns_to_v2_dna
    )

    migrate_unicorns_to_v2_dna_by_id_range_parser = subcommands.add_parser(
        "migrate-unicorns-to-v2-dna-by-id-range"
    )
    add_default_arguments(migrate_unicorns_to_v2_dna_by_id_range_parser, True)
    migrate_unicorns_to_v2_dna_by_id_range_parser.add_argument(
        "--first-token-id-arg", required=True, help="Type: uint256", type=int
    )
    migrate_unicorns_to_v2_dna_by_id_range_parser.add_argument(
        "--last-token-id-arg", required=True, help="Type: uint256", type=int
    )
    migrate_unicorns_to_v2_dna_by_id_range_parser.add_argument(
        "--first-names-arg", required=True, help="Type: uint16[]", nargs="+"
    )
    migrate_unicorns_to_v2_dna_by_id_range_parser.add_argument(
        "--last-names-arg", required=True, help="Type: uint16[]", nargs="+"
    )
    migrate_unicorns_to_v2_dna_by_id_range_parser.add_argument(
        "--bypass-dna-events-arg",
        required=True,
        help="Type: bool",
        type=boolean_argument_type,
    )
    migrate_unicorns_to_v2_dna_by_id_range_parser.set_defaults(
        func=handle_migrate_unicorns_to_v2_dna_by_id_range
    )

    rollback_v2_dna_to_v1_dna_parser = subcommands.add_parser(
        "rollback-v2-dna-to-v1-dna"
    )
    add_default_arguments(rollback_v2_dna_to_v1_dna_parser, True)
    rollback_v2_dna_to_v1_dna_parser.add_argument(
        "--token-ids-arg", required=True, help="Type: uint256[]", nargs="+"
    )
    rollback_v2_dna_to_v1_dna_parser.add_argument(
        "--bypass-dna-events-arg",
        required=True,
        help="Type: bool",
        type=boolean_argument_type,
    )
    rollback_v2_dna_to_v1_dna_parser.add_argument(
        "--force-arg", required=True, help="Type: bool", type=boolean_argument_type
    )
    rollback_v2_dna_to_v1_dna_parser.set_defaults(func=handle_rollback_v2_dna_to_v1_dna)

    set_target_dna_version_parser = subcommands.add_parser("set-target-dna-version")
    add_default_arguments(set_target_dna_version_parser, True)
    set_target_dna_version_parser.add_argument(
        "--version-number-arg", required=True, help="Type: uint256", type=int
    )
    set_target_dna_version_parser.set_defaults(func=handle_set_target_dna_version)

    return parser


def main() -> None:
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
