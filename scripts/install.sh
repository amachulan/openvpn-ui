#!/usr/bin/env bash
# Install vpnctl on a host that already has OpenVPN from angristan/openvpn-install.
set -euo pipefail

REPO_URL="${VPNCTL_REPO_URL:-https://github.com/amachulan/vpnctl.git}"
INSTALL_DIR="${VPNCTL_INSTALL_DIR:-/opt/vpnctl}"
PYTHON="${VPNCTL_PYTHON:-python3}"
# Nested pip (build isolation) only sees the env var, not --default-timeout.
export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-180}"
PIP_INDEX="${VPNCTL_PIP_INDEX:-}"
UPGRADE_PIP="${VPNCTL_UPGRADE_PIP:-0}"

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

apt-get update -y
apt-get install -y "${PYTHON}-venv" "${PYTHON}-setuptools" "${PYTHON}-wheel" git

if [[ -d "${INSTALL_DIR}/.git" ]]; then
  git -C "${INSTALL_DIR}" pull --ff-only
else
  git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

"${PYTHON}" -m venv "${INSTALL_DIR}/.venv"
# shellcheck disable=SC1091
source "${INSTALL_DIR}/.venv/bin/activate"

pip_args=(--disable-pip-version-check --default-timeout="${PIP_DEFAULT_TIMEOUT}")
if [[ -n "${PIP_INDEX}" ]]; then
  pip_args+=(-i "${PIP_INDEX}")
  export PIP_INDEX_URL="${PIP_INDEX}"
fi

pip_retry() {
  local attempt=1
  local max=5
  while true; do
    if pip "${pip_args[@]}" "$@"; then
      return 0
    fi
    if (( attempt >= max )); then
      echo "pip failed after ${max} attempts (cannot reach PyPI)." >&2
      echo "Check: curl -I https://pypi.org/simple/pip/" >&2
      echo "Retry with: export PIP_DEFAULT_TIMEOUT=300" >&2
      echo "Or a mirror: export VPNCTL_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple" >&2
      return 1
    fi
    echo "pip failed (attempt ${attempt}/${max}), retrying in $((attempt * 5))s..." >&2
    sleep $((attempt * 5))
    attempt=$((attempt + 1))
  done
}

# Upgrading pip itself often hangs on flaky PyPI links; skip by default.
if [[ "${UPGRADE_PIP}" == "1" ]]; then
  pip_retry install -U pip setuptools wheel
else
  # Seed build tools inside the venv when PyPI is slow (helps --no-build-isolation).
  pip_retry install setuptools wheel || true
fi

# Prefer no build isolation so we do not spawn a second pip with default 15s timeout.
if pip_retry install --no-build-isolation "${INSTALL_DIR}"; then
  :
else
  echo "Retrying with build isolation..." >&2
  pip_retry install "${INSTALL_DIR}"
fi

ln -sfn "${INSTALL_DIR}/.venv/bin/vpnctl" /usr/local/bin/vpnctl

vpnctl install --systemd

systemctl daemon-reload
systemctl enable --now vpnctl

echo
echo "vpnctl is running on http://127.0.0.1:8080/"
echo "API token is in /etc/vpnctl/config.yaml (api.token)."
echo "To expose over VPN, set api.host / allow_from_vpn in that file and restart."
