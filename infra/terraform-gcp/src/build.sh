#!/usr/bin/env bash
# Builds the deployment zips Terraform reads at PLAN time.
#
# `data.archive_file`/`filebase64sha256` in modules/tools and modules/approval read these
# files while the plan is being computed, so a missing zip fails the plan rather than the
# apply. Run this before every plan.
#
# ---------------------------------------------------------------------------
# How this differs from terraform-aws/src/build.sh, and why
# ---------------------------------------------------------------------------
#
# The AWS script pip-installs dependencies INTO each package, with an explicit
# --platform/--python-version, because a Lambda zip is the final artifact — whatever is not
# in it does not exist at runtime, and wheels resolved for the build machine are how you
# get an ImportError that only appears after deploy.
#
# Cloud Functions does not work that way. The zip is SOURCE, not an artifact: Cloud Build
# unpacks it, reads requirements.txt, and installs against the real runtime image. So this
# script must NOT vendor wheels — doing so would ship a Mac's binaries into a Linux build
# and shadow what Cloud Build resolves correctly on its own. It copies source and lets
# requirements.txt travel with it.
#
# The other direction of the same difference: the Lambda runtime preinstalls boto3, so the
# AWS packages are mostly dependency-free. The Cloud Functions python312 runtime ships
# essentially nothing beyond functions-framework, so here every package has a
# requirements.txt and every google-cloud import is declared. An undeclared import is a
# cold-start failure on a deploy that reported success.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SRC_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
STAGE_DIR="${BUILD_DIR}/.stage"

PACKAGES=(retrieve reason process_refund approval_validator approval_executor emit_trace)

rm -rf "${STAGE_DIR}"
mkdir -p "${BUILD_DIR}" "${STAGE_DIR}"

for package in "${PACKAGES[@]}"; do
  if [[ ! -d "${SRC_DIR}/${package}" ]]; then
    echo "error: ${SRC_DIR}/${package} does not exist" >&2
    exit 1
  fi

  # Cloud Functions resolves the entry point from a top-level main.py, so the handler file
  # is named main.py in every package rather than index.py as on AWS. A package missing one
  # deploys and then 404s on every invocation.
  if [[ ! -f "${SRC_DIR}/${package}/main.py" ]]; then
    echo "error: ${SRC_DIR}/${package}/main.py is required — Cloud Functions looks for it by name" >&2
    exit 1
  fi

  if [[ ! -f "${SRC_DIR}/${package}/requirements.txt" ]]; then
    echo "error: ${SRC_DIR}/${package}/requirements.txt is required — the runtime preinstalls nothing" >&2
    exit 1
  fi

  stage="${STAGE_DIR}/${package}"
  mkdir -p "${stage}"
  cp "${SRC_DIR}/${package}"/*.py "${stage}/"
  cp "${SRC_DIR}/${package}/requirements.txt" "${stage}/"

  # Shared modules are copied in flat, beside main.py, so `from agentic_trace import ...`
  # resolves without a package prefix or a sys.path change.
  cp "${SRC_DIR}/shared"/*.py "${stage}/"

  find "${stage}" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

  rm -f "${BUILD_DIR}/${package}.zip"
  # -X drops extra file attributes so the same source produces the same archive, which
  # keeps the object hash from churning and redeploying unchanged functions.
  (cd "${stage}" && zip -qrX "${BUILD_DIR}/${package}.zip" .)

  printf '%-24s %s\n' "${package}.zip" "$(du -h "${BUILD_DIR}/${package}.zip" | cut -f1)"
done

rm -rf "${STAGE_DIR}"
echo
echo "Built into ${BUILD_DIR}. The package_path values in terraform.tfvars point here."
