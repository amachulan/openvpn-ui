#!/usr/bin/env bash
# Install vpnctl on a host that already has OpenVPN from angristan/openvpn-install.
set -euo pipefail

REPO_URL="${VPNCTL_REPO_URL:-https://github.com/amachulan/vpnctl.git}"
INSTALL_DIR="${VPNCTL_INSTALL_DIR:-/opt/vpnctl}"
PYTHON="${VPNCTL_PYTHON:-python3}"
export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-60}"
PIP_INDEX="${VPNCTL_PIP_INDEX:-}"
UPGRADE_PIP="${VPNCTL_UPGRADE_PIP:-0}"
INSTALL_SH_REV="2026-08-07c"

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

# When launched via `curl | bash`, refresh the repo then re-exec the local script
# so CDN/cache cannot keep running a stale installer.
if [[ "${1:-}" != "--from-local" ]]; then
  apt-get update -y
  apt-get install -y git curl
  if [[ -d "${INSTALL_DIR}/.git" ]]; then
    git -C "${INSTALL_DIR}" pull --ff-only
  else
    git clone "${REPO_URL}" "${INSTALL_DIR}"
  fi
  echo "Re-exec local installer: ${INSTALL_DIR}/scripts/install.sh (${INSTALL_SH_REV} bootstrap)"
  exec bash "${INSTALL_DIR}/scripts/install.sh" --from-local
fi

echo "vpnctl install.sh rev ${INSTALL_SH_REV}"

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

pick_pip_index
# Prefer env config over CLI flags: some pip builds reject -i/--index-url oddly.
export PIP_INDEX_URL="${PIP_INDEX}"

if [[ ! -d "${INSTALL_DIR}/.git" ]]; then
  git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

"${PYTHON}" -m venv "${INSTALL_DIR}/.venv"
VENV_PY="${INSTALL_DIR}/.venv/bin/python"

pip_install() {
  local attempt=1
  local max=4
  while true; do
    # No -i / --index-url on CLI; PIP_INDEX_URL + PIP_DEFAULT_TIMEOUT are enough.
    if "${VENV_PY}" -m pip install --disable-pip-version-check "$@"; then
      return 0
    fi
    if (( attempt >= max )); then
      echo "pip failed after ${max} attempts." >&2
      echo "Index used: ${PIP_INDEX_URL}" >&2
      echo "Check: curl -I ${PIP_INDEX_URL}/pip/" >&2
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

if pip_install --no-build-isolation "${INSTALL_DIR}"; then
  :
else
  echo "Retrying with build isolation..." >&2
  pip_install "${INSTALL_DIR}"
fi

ln -sfn "${INSTALL_DIR}/.venv/bin/vpnctl" /usr/local/bin/vpnctl

vpnctl install --systemd

systemctl daemon-reload
systemctl enable --now vpnctl

echo
echo "vpnctl is running on http://127.0.0.1:8080/"
echo "API token is in /etc/vpnctl/config.yaml (api.token)."
echo "Pip index used: ${PIP_INDEX_URL}"
echo "To expose over VPN, set api.host / allow_from_vpn in that file and restart."
