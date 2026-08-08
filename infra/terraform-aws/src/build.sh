#!/usr/bin/env bash
# Builds the deployment zips Terraform reads at PLAN time.
#
# `filebase64sha256` in modules/tools and modules/approval reads these files while the
# plan is being computed, so a missing zip fails the plan rather than the apply. Run this
# before every plan.
#
# Each package is a plain directory plus the shared modules copied in beside it. Packages
# stay dependency-free wherever possible — boto3 and botocore already ship in the Lambda
# Python runtime, and a zip you can still read in the console during an incident is worth
# protecting. A package that genuinely needs a library declares it in its own
# requirements.txt and only that package pays the cost; today only `reason` does.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SRC_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
STAGE_DIR="${BUILD_DIR}/.stage"

# Wheels are resolved for the Lambda runtime, not for whatever machine runs this script.
# Building on a Mac and shipping native wheels to Amazon Linux is the classic way to get
# an ImportError that only appears after deploy.
LAMBDA_PLATFORM="${LAMBDA_PLATFORM:-manylinux2014_x86_64}"
LAMBDA_PYTHON="${LAMBDA_PYTHON:-3.12}"

# `python3 -m pip` rather than a bare `pip`: plenty of systems (Homebrew among them) ship
# pip3 without a `pip` shim, and the module form always matches the interpreter it runs
# under. PYTHON overrides it for a venv or pyenv build.
PYTHON="${PYTHON:-python3}"

PACKAGES=(retrieve reason process_refund approval_validator approval_executor emit_trace)

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

  if [[ -f "${SRC_DIR}/${package}/requirements.txt" ]]; then
    # --only-binary=:all: with an explicit platform: pip must not fall back to building
    # a wheel from source against the local interpreter, which is exactly how a package
    # ends up carrying the build machine's architecture.
    "${PYTHON}" -m pip install \
      --quiet \
      --requirement "${SRC_DIR}/${package}/requirements.txt" \
      --target "${stage}" \
      --platform "${LAMBDA_PLATFORM}" \
      --python-version "${LAMBDA_PYTHON}" \
      --only-binary=:all: \
      --upgrade

    # Metadata directories are reproducibility noise: they carry install timestamps that
    # change source_code_hash on every build and redeploy functions that did not change.
    find "${stage}" -maxdepth 1 -name '*.dist-info' -type d -exec rm -rf {} +
    find "${stage}" -name '__pycache__' -type d -exec rm -rf {} +
  fi

  rm -f "${BUILD_DIR}/${package}.zip"
  # -X drops extra file attributes so the same source produces the same archive, which
  # keeps source_code_hash from churning and redeploying unchanged functions.
  (cd "${stage}" && zip -qrX "${BUILD_DIR}/${package}.zip" .)

  printf '%-20s %s\n' "${package}.zip" "$(du -h "${BUILD_DIR}/${package}.zip" | cut -f1)"
done

rm -rf "${STAGE_DIR}"
echo
echo "Built into ${BUILD_DIR}. The package_path values in terraform.tfvars point here."
