#!/usr/bin/env bash
# Install or upgrade vpnctl. Safe to re-run (idempotent one-liner).
# Preserves /etc/vpnctl/config.yaml; refreshes code under /opt/vpnctl and restarts the service.
set -euo pipefail

REPO_URL="${VPNCTL_REPO_URL:-https://github.com/amachulan/vpnctl.git}"
INSTALL_DIR="${VPNCTL_INSTALL_DIR:-/opt/vpnctl}"
PYTHON="${VPNCTL_PYTHON:-python3}"
export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-60}"
export VPNCTL_INSTALL_DIR="${INSTALL_DIR}"
PIP_INDEX="${VPNCTL_PIP_INDEX:-}"
UPGRADE_PIP="${VPNCTL_UPGRADE_PIP:-0}"
INSTALL_SH_REV="2026-08-07e"

PIP_MIRRORS=(
  "https://pypi.org/simple"
  "https://pypi.tuna.tsinghua.edu.cn/simple"
  "https://mirrors.aliyun.com/pypi/simple"
  "https://pypi.mirrors.ustc.edu.cn/simple"
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

if ! command -v "${PYTHON}" >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

if [[ ! -d /etc/openvpn/server/easy-rsa ]]; then
  echo "angristan OpenVPN layout not found at /etc/openvpn/server/easy-rsa" >&2
  echo "Install OpenVPN first: https://github.com/angristan/openvpn-install" >&2
  exit 1
fi

sync_repo() {
  apt-get update -y
  apt-get install -y git curl
  if [[ -d "${INSTALL_DIR}/.git" ]]; then
    git -C "${INSTALL_DIR}" fetch --prune origin
    git -C "${INSTALL_DIR}" checkout -B main origin/main
    git -C "${INSTALL_DIR}" reset --hard origin/main
    git -C "${INSTALL_DIR}" clean -fd
  else
    rm -rf "${INSTALL_DIR}"
    git clone --branch main "${REPO_URL}" "${INSTALL_DIR}"
  fi
}

# curl|bash bootstrap: sync repo, then always re-exec the local script (avoids CDN stale copies).
if [[ "${1:-}" != "--from-local" ]]; then
  sync_repo
  echo "Re-exec local installer (${INSTALL_SH_REV} bootstrap) → ${INSTALL_DIR}/scripts/install.sh"
  exec bash "${INSTALL_DIR}/scripts/install.sh" --from-local
fi

echo "vpnctl install.sh rev ${INSTALL_SH_REV} (idempotent install/upgrade)"

pick_pip_index() {
  if [[ -n "${PIP_INDEX}" ]]; then
    echo "Using VPNCTL_PIP_INDEX=${PIP_INDEX}"
    return 0
  fi
  local url
  for url in "${PIP_MIRRORS[@]}"; do
    echo "Probing PyPI index: ${url}"
    if curl -fsSL --connect-timeout 5 --max-time 15 "${url}/pip/" >/dev/null 2>&1; then
      PIP_INDEX="${url}"
      echo "Selected pip index: ${PIP_INDEX}"
      return 0
    fi
    echo "  unreachable"
  done
  echo "WARNING: no pip index responded quickly; falling back to pypi.org" >&2
  PIP_INDEX="https://pypi.org/simple"
}

apt-get install -y "${PYTHON}-venv" "${PYTHON}-setuptools" "${PYTHON}-wheel" curl git

# Repo should already be synced by bootstrap; refresh again in case of direct --from-local.
if [[ -d "${INSTALL_DIR}/.git" ]]; then
  git -C "${INSTALL_DIR}" fetch --prune origin
  git -C "${INSTALL_DIR}" checkout -B main origin/main
  git -C "${INSTALL_DIR}" reset --hard origin/main
else
  git clone --branch main "${REPO_URL}" "${INSTALL_DIR}"
fi

pick_pip_index
export PIP_INDEX_URL="${PIP_INDEX}"

"${PYTHON}" -m venv "${INSTALL_DIR}/.venv"
VENV_PY="${INSTALL_DIR}/.venv/bin/python"

pip_install() {
  local attempt=1
  local max=4
  while true; do
    if "${VENV_PY}" -m pip install --disable-pip-version-check "$@"; then
      return 0
    fi
    if (( attempt >= max )); then
      echo "pip failed after ${max} attempts." >&2
      echo "Index used: ${PIP_INDEX_URL}" >&2
      echo "Override: VPNCTL_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple" >&2
      return 1
    fi
    echo "pip failed (attempt ${attempt}/${max}), retrying in $((attempt * 3))s..." >&2
    sleep $((attempt * 3))
    attempt=$((attempt + 1))
  done
}

if [[ "${UPGRADE_PIP}" == "1" ]]; then
  pip_install -U pip setuptools wheel
else
  pip_install setuptools wheel
fi

# Always reinstall package from the synced tree so upgrades pick up new code.
if pip_install --upgrade --force-reinstall --no-build-isolation "${INSTALL_DIR}"; then
  :
else
  echo "Retrying with build isolation..." >&2
  pip_install --upgrade --force-reinstall "${INSTALL_DIR}"
fi

ln -sfn "${INSTALL_DIR}/.venv/bin/vpnctl" /usr/local/bin/vpnctl

CONFIG_EXISTED=0
[[ -f /etc/vpnctl/config.yaml ]] && CONFIG_EXISTED=1

vpnctl install --systemd

systemctl daemon-reload
systemctl enable vpnctl
systemctl restart vpnctl

# Give the service a moment, then show status.
sleep 1
if systemctl is-active --quiet vpnctl; then
  STATUS_LINE="active"
else
  STATUS_LINE="NOT active — run: journalctl -u vpnctl -n 50 --no-pager"
fi

TOKEN="$(awk '/^[[:space:]]*token:/{print $2; exit}' /etc/vpnctl/config.yaml 2>/dev/null || true)"
HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
[[ -z "${HOST_IP}" ]] && HOST_IP="SERVER_IP"

echo
if [[ "${CONFIG_EXISTED}" -eq 1 ]]; then
  echo "vpnctl upgraded and restarted (${STATUS_LINE})."
else
  echo "vpnctl installed and started (${STATUS_LINE})."
fi
echo "  UI:     http://${HOST_IP}:8080/"
echo "  Token:  ${TOKEN:-see /etc/vpnctl/config.yaml}"
echo "  Config: /etc/vpnctl/config.yaml (preserved across upgrades)"
echo "  Code:   ${INSTALL_DIR}"
