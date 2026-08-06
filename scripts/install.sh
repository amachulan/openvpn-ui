#!/usr/bin/env bash
# Install vpnctl on a host that already has OpenVPN from angristan/openvpn-install.
set -euo pipefail

REPO_URL="${VPNCTL_REPO_URL:-https://github.com/amachulan/vpnctl.git}"
INSTALL_DIR="${VPNCTL_INSTALL_DIR:-/opt/vpnctl}"
PYTHON="${VPNCTL_PYTHON:-python3}"

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
apt-get install -y "${PYTHON}-venv" git

if [[ -d "${INSTALL_DIR}/.git" ]]; then
  git -C "${INSTALL_DIR}" pull --ff-only
else
  git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

"${PYTHON}" -m venv "${INSTALL_DIR}/.venv"
# shellcheck disable=SC1091
source "${INSTALL_DIR}/.venv/bin/activate"
pip install -U pip
pip install "${INSTALL_DIR}"

ln -sfn "${INSTALL_DIR}/.venv/bin/vpnctl" /usr/local/bin/vpnctl

vpnctl install --systemd

systemctl daemon-reload
systemctl enable --now vpnctl

echo
echo "vpnctl is running on http://127.0.0.1:8080/"
echo "API token is in /etc/vpnctl/config.yaml (api.token)."
echo "Put nginx/caddy in front if you need remote access."
