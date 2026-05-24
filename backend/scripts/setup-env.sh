#!/usr/bin/env bash
# Create or update the conda environment for the autoresearch dashboard.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT}/environment.yml"
ENV_NAME="autoresearch-dashboard"

if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda not found. Install Miniconda or Anaconda first." >&2
  echo "  https://docs.conda.io/en/latest/miniconda.html" >&2
  exit 1
fi

if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "Updating conda env: ${ENV_NAME}"
  conda env update -f "${ENV_FILE}" --prune
else
  echo "Creating conda env: ${ENV_NAME}"
  conda env create -f "${ENV_FILE}"
fi

echo ""
echo "Done. Activate with:"
echo "  conda activate ${ENV_NAME}"
echo ""
echo "Then start the dashboard:"
echo "  ./bin/autoresearch-dashboard --project /path/to/your/project"
