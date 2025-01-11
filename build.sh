#!/usr/bin/env bash
VERSION="v1"
QUAY_DEST="quay.io/openshift/ci-public:registry-liveness-probe-${VERSION}"
GCR_HOST="us.gcr.io"
GCR_DEST="${GCR_HOST}/openshift-ci-data-analysis/registry-liveness-probe:${VERSION}"
# podman build . -t ${QUAY_DEST}
# podman push ${QUAY_DEST}
echo "Pushed image to ${QUAY_DEST}"

# In order to run in a google console scheduled task, we need to push
# to a GCR repository.
gcloud auth print-access-token | podman login -u oauth2accesstoken --password-stdin "https://${GCR_HOST}"
podman tag "${QUAY_DEST}" "${GCR_DEST}"
podman push "${GCR_DEST}"
echo "Pushed image to ${GCR_DEST}"
