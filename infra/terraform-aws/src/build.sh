#!/usr/bin/env bash
# Builds the deployment zips Terraform reads at PLAN time.
#
# `filebase64sha256` in modules/tools and modules/approval reads these files while the
# plan is being computed, so a missing zip fails the plan rather than the apply. Run this
# before every plan.
#
# Each package is a plain directory plus the shared modules copied in beside it. No pip,
# no wheels, no layers: boto3 and botocore already ship in the Lambda Python runtime, and
# a dependency-free zip is one you can still read in the console during an incident.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SRC_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
STAGE_DIR="${BUILD_DIR}/.stage"

PACKAGES=(retrieve process_refund approval_validator approval_executor)

rm -rf "${STAGE_DIR}"
mkdir -p "${BUILD_DIR}" "${STAGE_DIR}"

for package in "${PACKAGES[@]}"; do
  if [[ ! -d "${SRC_DIR}/${package}" ]]; then
    echo "error: ${SRC_DIR}/${package} does not exist" >&2
    exit 1
  fi

  stage="${STAGE_DIR}/${package}"
  mkdir -p "${stage}"
  cp "${SRC_DIR}/${package}"/*.py "${stage}/"
  cp "${SRC_DIR}/shared"/*.py "${stage}/"

  rm -f "${BUILD_DIR}/${package}.zip"
  # -X drops extra file attributes so the same source produces the same archive, which
  # keeps source_code_hash from churning and redeploying unchanged functions.
  (cd "${stage}" && zip -qrX "${BUILD_DIR}/${package}.zip" .)

  printf '%-20s %s\n' "${package}.zip" "$(du -h "${BUILD_DIR}/${package}.zip" | cut -f1)"
done

rm -rf "${STAGE_DIR}"
echo
echo "Built into ${BUILD_DIR}. The package_path values in terraform.tfvars point here."
