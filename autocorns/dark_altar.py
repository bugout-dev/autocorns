import argparse
import datetime
import json
import os
import sys
import time
from typing import Optional

import requests

from .GOFPFacet import add_default_arguments, handle_num_sessions


def handle_choices_for_session(args: argparse.Namespace) -> None:
    moonstream_access_token: Optional[str] = args.token
    if moonstream_access_token is None:
        moonstream_access_token = os.environ.get("MOONSTREAM_ACCESS_TOKEN")
    if moonstream_access_token is None:
        raise ValueError(
            "Please pass the --token argument or set the MOONSTREAM_ACCESS_TOKEN environment variable"
        )

    query_name = ""
    if args.blockchain == "mumbai":
        query_name = "garden_of_forking_path_choices"

    if not query_name:
        raise ValueError(f"Unsupported blockchain: {args.blockchain}")

    api_url = args.api.rstrip("/")
    request_url = f"{api_url}/queries/{query_name}/update_data"
    headers = {
        "Authorization": f"Bearer {moonstream_access_token}",
        "Content-Type": "application/json",
    }
    # Assume our clock is not drifting too much from AWS clocks.
    if_modified_since_datetime = datetime.datetime.utcnow()
    if_modified_since = if_modified_since_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")

    request_body = {
        "params": {"contract_address": args.address, "session_id": args.session_id}
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


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="The Dark Altar in the Dark Forest: Glory to the Shadowcorns!"
    )
    parser.set_defaults(func=lambda _: parser.print_help())

    subparsers = parser.add_subparsers()

    total_sessions_parser = subparsers.add_parser("total-sessions")
    add_default_arguments(total_sessions_parser, False)
    total_sessions_parser.set_defaults(func=handle_num_sessions)

    choices_for_session_parser = subparsers.add_parser("choices-for-session")
    choices_for_session_parser.add_argument(
        "--blockchain",
        choices=["mumbai", "polygon"],
        required=True,
        help="Blockchain that contract lives on",
    )
    choices_for_session_parser.add_argument(
        "-a", "--address", required=True, help="Address of smart contract"
    )
    choices_for_session_parser.add_argument(
        "--session-id",
        required=True,
        help="Session ID for which you want to retrieve choices",
    )
    choices_for_session_parser.add_argument(
        "--interval", type=float, default=2.0, help="Polling interval for updated data"
    )
    choices_for_session_parser.add_argument(
        "--max-retries",
        type=int,
        default=0,
        help="Maximum number of retries for data (0 means unlimited).",
    )
    choices_for_session_parser.add_argument(
        "-o",
        "--outfile",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="(Optional) file to write output to. Default: sys.stdout",
    )
    choices_for_session_parser.add_argument(
        "-t",
        "--token",
        required=False,
        default=None,
        help="Moonstream access token. If not passed, dark-altar uses the MOONSTREAM_ACCESS_TOKEN environment variable.",
    )
    choices_for_session_parser.add_argument(
        "--api",
        default="https://api.moonstream.to",
        help="Moonstream API URL (default: https://api.moonstream.to). Access token expected to be set as MOONSTREAM_ACCESS_TOKEN environment variable.",
    )

    choices_for_session_parser.set_defaults(func=handle_choices_for_session)

    return parser


if __name__ == "__main__":
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)
