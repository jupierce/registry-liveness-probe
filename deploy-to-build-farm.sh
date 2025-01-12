#!/usr/bin/env bash

set -e
set -o pipefail

if [ "$#" -lt 1 ]; then
  echo "Installs the registry-liveness-probe job on a build farm."
  echo "Usage: $0 <CLOUD NAME> [OC_CONTEXT]"
  exit 1
fi

if [ -z "$2" ]; then
  CONTEXT=""
else
  CONTEXT="--context=$2"
fi

CLOUD_VALUE="$1"

. info.env

REQUESTER_VALUE=$(oc "${CONTEXT}" whoami --show-server | tr -d '\n')
echo "Applying job with ${REQUESTER_VALUE} as cloud type ${CLOUD_VALUE}"
sed "s#CLOUD#${CLOUD_VALUE}#g; s#REQUESTER#${REQUESTER_VALUE}#g" cronjob.yaml | oc --as system:admin ${CONTEXT} -n ci apply -f -