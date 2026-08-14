#!/usr/bin/env bash
# Builds the deployment zips Terraform reads at PLAN time.
#
# `fileexists()` in envs/*/main.tf and `zip_deploy_file` in modules/tools and
# modules/approval read these paths while the plan is being computed, so a missing zip fails
# the plan rather than the apply. Run this before every plan.
#
# ---------------------------------------------------------------------------
# How this differs from the AWS and GCP scripts, and why
# ---------------------------------------------------------------------------
#
# AWS   pip-installs dependencies INTO the zip with an explicit --platform, because a Lambda
#       zip is the final artifact: whatever is not in it does not exist at runtime.
# GCP   ships source only, because Cloud Build unpacks the zip and installs requirements.txt
#       against the real runtime image.
# Azure sits with GCP, for a different reason. `zip_deploy_file` with
#       SCM_DO_BUILD_DURING_DEPLOYMENT enabled hands the zip to Oryx, which runs pip on the
#       build server. Vendoring wheels here would ship a Mac's binaries into a Linux app and
#       shadow what Oryx resolves correctly on its own.
#
# The consequence to be aware of: an undeclared import is not caught by this script. It is
# caught at cold start, on an app that deployed successfully. Hence the requirements.txt
# check below being fatal rather than a warning.
#
# ---------------------------------------------------------------------------
# What each package must contain
# ---------------------------------------------------------------------------
#
#   function_app.py   the v2 binding, discovered by that exact name. Missing it produces an
#                     app that deploys and then 404s on every route.
#   handler.py        all the logic, importable without azure-functions or a host — which is
#                     what makes tests/test_handlers.py possible.
#   host.json         required at the package root. Note it disables Application Insights
#                     adaptive sampling: sampling silently DROPS trace records, and every
#                     alert in modules/observability counts events. A sampled pipeline makes
#                     those alerts undercount by an amount nobody can see.
#   requirements.txt  the worker ships azure-functions and nothing else.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SRC_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
STAGE_DIR="${BUILD_DIR}/.stage"

PACKAGES=(retrieve reason process_refund approval_validator approval_executor emit_trace)

REQUIRED_FILES=(function_app.py handler.py host.json requirements.txt)

rm -rf "${STAGE_DIR}"
mkdir -p "${BUILD_DIR}" "${STAGE_DIR}"

for package in "${PACKAGES[@]}"; do
  if [[ ! -d "${SRC_DIR}/${package}" ]]; then
    echo "error: ${SRC_DIR}/${package} does not exist" >&2
    exit 1
  fi

  for required in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "${SRC_DIR}/${package}/${required}" ]]; then
      echo "error: ${SRC_DIR}/${package}/${required} is required — see the header in this script" >&2
      exit 1
    fi
  done

  stage="${STAGE_DIR}/${package}"
  mkdir -p "${stage}"
  cp "${SRC_DIR}/${package}"/*.py "${stage}/"
  cp "${SRC_DIR}/${package}/host.json" "${stage}/"
  cp "${SRC_DIR}/${package}/requirements.txt" "${stage}/"

  # Shared modules are copied in flat, beside function_app.py, so `from agentic_trace import
  # ...` resolves without a package prefix or a sys.path change.
  cp "${SRC_DIR}/shared"/*.py "${stage}/"

  find "${stage}" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

  rm -f "${BUILD_DIR}/${package}.zip"
  # -X drops extra file attributes so the same source produces the same archive, which keeps
  # the deployment hash from churning and redeploying unchanged apps.
  (cd "${stage}" && zip -qrX "${BUILD_DIR}/${package}.zip" .)

  printf '%-24s %s\n' "${package}.zip" "$(du -h "${BUILD_DIR}/${package}.zip" | cut -f1)"
done

rm -rf "${STAGE_DIR}"
echo
echo "Built into ${BUILD_DIR}. The package_path values in terraform.tfvars point here."
