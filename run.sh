#!/usr/bin/env bash
# Prérequis : Docker uniquement. Pas de Python, pas de venv, pas d'Ansible en local.
#
# Usage :
#   ./run.sh          → lance molecule test complet
#   ./run.sh shell    → ouvre un shell dans le runner (mode dev)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')
IMAGE="molecule-minio-runner"
MODE="${1:-test}"

if ! command -v docker &>/dev/null; then
  echo "Erreur : Docker n'est pas installé." >&2
  exit 1
fi

if [ -S "${HOME}/.docker/run/docker.sock" ]; then
  DOCKER_SOCK="${HOME}/.docker/run/docker.sock"
else
  DOCKER_SOCK="/var/run/docker.sock"
fi

DOCKER_RUN=(
  docker run --rm -it
  --platform "linux/${ARCH}"
  -v "${SCRIPT_DIR}:/workspace"
  -v "${DOCKER_SOCK}:/var/run/docker.sock"
  --name molecule
  -w /workspace
  molecule:latest
)

if [ "${MODE}" = "shell" ]; then
  echo "==> Shell interactif — tu es dans /workspace"
  echo "    Commandes utiles :"
  echo "      cd roles/minio"
  echo "      molecule create"
  echo "      molecule prepare"
  echo "      molecule converge"
  echo "      molecule verify"
  echo "      molecule destroy"
  "${DOCKER_RUN[@]}" bash
else
  echo "==> Lancement des tests..."
  "${DOCKER_RUN[@]}" bash -c "
    set -euo pipefail
    cd /workspace
    ansible-galaxy collection build --output-path /tmp/ --force
    ansible-galaxy collection install /tmp/poc-minio-*.tar.gz --force
    cd roles/configure && molecule test
  "
fi
