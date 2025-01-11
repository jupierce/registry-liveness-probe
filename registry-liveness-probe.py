#!/usr/bin/env python3
import datetime
import os
import argparse
import subprocess
from google.cloud import bigquery

table_id = "openshift-gce-devel.ci_analysis_us.registry_liveness"

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Attempt to access the pullspec and record the result in bigquery"
    )

    # Define arguments
    parser.add_argument(
        "--pullspec",
        required=True,
        help="Specify the pullspec, e.g., quay.io/openshift/ci:test"
    )
    parser.add_argument(
        "--requester",
        required=True,
        help="Specify the requester name, e.g., gcp"
    )

    parser.add_argument(
        "--cloud",
        required=False,
        help="The name of the cloud the requester is in",
        default='local'
    )

    parser.add_argument(
        "--credentials",
        required=False,
        help="Path to the Google Cloud credentials JSON file"
    )

    # Parse the arguments
    args = parser.parse_args()

    if args.credentials:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.credentials

    # Initialize BigQuery client
    client = bigquery.Client()

    # Example: Print confirmation of client setup (replace with actual BigQuery operations as needed)
    print("BigQuery client initialized.")

    # Print the parsed arguments (for demonstration purposes)
    print(f"Pullspec: {args.pullspec}")
    print(f"Requester: {args.requester}")

    process = subprocess.run(f'oc image info --filter-by-os=amd64 {args.pullspec}', stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    row = {
        "issued": datetime.datetime.utcnow().isoformat(),
        "requester": args.requester,
        "pullspec": args.pullspec,
        "success_val": 1 if process.returncode == 0 else 0,
        "return_code": process.returncode,
        "stderr": process.stderr,
        "cloud": args.cloud,
    }

    errors = client.insert_rows_json(table_id, [row])

    if errors:
        print(f"Errors occurred while inserting rows: {errors}")
    else:
        print(f"Row successfully inserted into BigQuery: {row}")
