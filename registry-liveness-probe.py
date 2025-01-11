#!/usr/bin/env python3
import datetime
import os
import argparse
import subprocess
import sys
import random
import tempfile

import boto3
from google.cloud import bigquery

DEFAULT_PULLSPECS = [
    'registry.redhat.io/redhat/redhat-operator-index:v4.17',
    'quay.io/openshift-release-dev/ocp-release:4.17.12-x86_64',
    'quay.io/openshift-release-dev/ocp-v4.0-art-dev:sha256-767b226c7f2026abcc98cd36b11b2e15c5fb153bb363bc5f35834eba94ccf546',
]

table_id = "openshift-ci-data-analysis.registry_liveness.queries"


def read_aws_secret(secret_name):
    """Retrieve the secret value from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response.get('SecretString', '')
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve AWS secret '{secret_name}': {e}")


def write_temp_file(content):
    """Write content to a temporary file and return the file path."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    with open(temp_file.name, 'w') as file:
        file.write(content)
    return temp_file.name


def process_argument(value):
    """Process the argument value, either reading from AWS Secrets Manager or using a local file."""
    if value.startswith("aws@"):
        secret_name = value.split("@", 1)[1]
        secret_content = read_aws_secret(secret_name)
        temp_file_path = write_temp_file(secret_content)
        print(f"Temporary file created: {temp_file_path}")
        return temp_file_path
    else:
        if not os.path.exists(value):
            raise FileNotFoundError(f"Local file not found: {value}")
        print(f"Using local file: {value}")
        return value


if __name__ == '__main__':

    print(f'Arguments: {sys.argv}')

    parser = argparse.ArgumentParser(
        description="Attempt to access the pullspec and record the result in bigquery"
    )

    # Define arguments
    parser.add_argument(
        "--pullspec",
        required=False,
        action="append",
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
        "--bq-credentials",
        required=False,
        help=f"Path to the Google Cloud credentials JSON file to write to BigQuery {table_id}"
    )

    parser.add_argument(
        "--registry-config",
        required=False,
        help=f"Path to registry configuration file to use for pullspec query"
    )

    args = parser.parse_args()

    if args.bq_credentials:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = process_argument(args.bq_credentials)

    # Initialize BigQuery client
    client = bigquery.Client()

    # Example: Print confirmation of client setup (replace with actual BigQuery operations as needed)
    print("BigQuery client initialized.")

    registry_config_param = ''
    if args.registry_config:
        # If a registry config file was specified, pass it to oc
        registry_config_param = f'--registry-config={process_argument(args.registry_config)}'

    if args.pullspec:
        randomized_pullspecs = args.pullspec[:]
    else:
        randomized_pullspecs = list(DEFAULT_PULLSPECS)

    # Randomize the order of pullspecs so that we can determine whether being the first
    # to be accessed is different from the next.
    random.shuffle(randomized_pullspecs)

    successes = 0
    rows = list()
    for order, pullspec in enumerate(randomized_pullspecs):
        process = subprocess.run(f'oc image info {registry_config_param} --filter-by-os=amd64 {pullspec}', stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        row = {
            "issued": datetime.datetime.utcnow().isoformat(),
            "requester": args.requester,
            "pullspec": pullspec,
            "success_val": 1 if process.returncode == 0 else 0,
            "return_code": process.returncode,
            "stderr": process.stderr,
            "cloud": args.cloud,
            "order": order,
        }

        if process.returncode == 0:
            successes += 1
        rows.append(row)

    errors = client.insert_rows_json(table_id, rows)

    if errors:
        print(f"Errors occurred while inserting rows: {errors}")
        exit(1)
    else:
        print(f"Rows successfully inserted into BigQuery: {rows}")

    if successes > 0 and successes != len(randomized_pullspecs):
        # If one of the registries is failing, exit with an error
        # code. The Google Cloud Run is configured to rerun up
        # to 3 times if an error is encountered. This will cause
        # the probe to run even more when a registry is down.
        exit(1)
