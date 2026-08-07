#!/usr/bin/env bash
# Install or upgrade vpnctl. Safe to re-run (idempotent one-liner).
# Preserves /etc/vpnctl/config.yaml; refreshes code under /opt/vpnctl and restarts the service.
#
# Fast re-run (skip apt + mirror probes + setuptools bootstrap):
#   curl -fsSL ".../install.sh?$(date +%s)" | sudo env VPNCTL_SKIP_DEPS=1 bash
#   sudo bash /opt/vpnctl/scripts/install.sh --from-local --skip-deps
set -euo pipefail

REPO_URL="${VPNCTL_REPO_URL:-https://github.com/amachulan/vpnctl.git}"
INSTALL_DIR="${VPNCTL_INSTALL_DIR:-/opt/vpnctl}"
PYTHON="${VPNCTL_PYTHON:-python3}"
export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-60}"
export VPNCTL_INSTALL_DIR="${INSTALL_DIR}"
PIP_INDEX="${VPNCTL_PIP_INDEX:-}"
UPGRADE_PIP="${VPNCTL_UPGRADE_PIP:-0}"
SKIP_DEPS="${VPNCTL_SKIP_DEPS:-0}"
INSTALL_SH_REV="2026-08-07f"
PIP_INDEX_CACHE="${INSTALL_DIR}/.pip-index"

PIP_MIRRORS=(
  "https://pypi.org/simple"
  "https://pypi.tuna.tsinghua.edu.cn/simple"
  "https://mirrors.aliyun.com/pypi/simple"
  "https://pypi.mirrors.ustc.edu.cn/simple"
)

FROM_LOCAL=0
for arg in "$@"; do
  case "${arg}" in
    --from-local) FROM_LOCAL=1 ;;
    --skip-deps) SKIP_DEPS=1 ;;
  esac
done
export VPNCTL_SKIP_DEPS="${SKIP_DEPS}"

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
  if [[ "${SKIP_DEPS}" != "1" ]]; then
    apt-get update -y
    apt-get install -y git curl
  elif ! command -v git >/dev/null 2>&1; then
    echo "git missing; run a full install once without VPNCTL_SKIP_DEPS=1" >&2
    exit 1
  fi
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

if [[ "${FROM_LOCAL}" != "1" ]]; then
  sync_repo
  echo "Re-exec local installer (${INSTALL_SH_REV} bootstrap) → ${INSTALL_DIR}/scripts/install.sh"
  if [[ "${SKIP_DEPS}" == "1" ]]; then
    exec bash "${INSTALL_DIR}/scripts/install.sh" --from-local --skip-deps
  fi
  exec bash "${INSTALL_DIR}/scripts/install.sh" --from-local
fi

echo "vpnctl install.sh rev ${INSTALL_SH_REV} (idempotent install/upgrade)"
if [[ "${SKIP_DEPS}" == "1" ]]; then
  echo "SKIP_DEPS=1 — skipping apt and mirror probes"
fi

pick_pip_index() {
  if [[ -n "${PIP_INDEX}" ]]; then
    echo "Using VPNCTL_PIP_INDEX=${PIP_INDEX}"
    return 0
  fi
  if [[ -f "${PIP_INDEX_CACHE}" ]]; then
    PIP_INDEX="$(tr -d '[:space:]' < "${PIP_INDEX_CACHE}")"
    if [[ -n "${PIP_INDEX}" ]]; then
      echo "Using cached pip index: ${PIP_INDEX}"
      return 0
    fi
  fi
  if [[ "${SKIP_DEPS}" == "1" ]]; then
    PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
    echo "SKIP_DEPS: defaulting pip index to ${PIP_INDEX}"
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

if [[ "${SKIP_DEPS}" != "1" ]]; then
  apt-get install -y "${PYTHON}-venv" "${PYTHON}-setuptools" "${PYTHON}-wheel" curl git
fi

if [[ -d "${INSTALL_DIR}/.git" ]]; then
  git -C "${INSTALL_DIR}" fetch --prune origin
  git -C "${INSTALL_DIR}" checkout -B main origin/main
  git -C "${INSTALL_DIR}" reset --hard origin/main
else
  git clone --branch main "${REPO_URL}" "${INSTALL_DIR}"
fi

pick_pip_index
export PIP_INDEX_URL="${PIP_INDEX}"
printf '%s\n' "${PIP_INDEX}" > "${PIP_INDEX_CACHE}"

if [[ ! -x "${INSTALL_DIR}/.venv/bin/python" ]]; then
  if [[ "${SKIP_DEPS}" == "1" ]]; then
    echo "venv missing; run a full install once without SKIP_DEPS" >&2
    exit 1
  fi
  "${PYTHON}" -m venv "${INSTALL_DIR}/.venv"
elif [[ "${SKIP_DEPS}" != "1" ]]; then
  "${PYTHON}" -m venv "${INSTALL_DIR}/.venv"
fi
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

if [[ "${SKIP_DEPS}" != "1" ]]; then
  if [[ "${UPGRADE_PIP}" == "1" ]]; then
    pip_install -U pip setuptools wheel
  else
    pip_install setuptools wheel
  fi
fi

# Reinstall package from the synced tree. With SKIP_DEPS, prefer --no-deps (code-only);
# fall back to full resolve if that fails (e.g. first run / missing wheels).
if [[ "${SKIP_DEPS}" == "1" ]] && pip_install --upgrade --force-reinstall --no-deps --no-build-isolation "${INSTALL_DIR}"; then
  :
elif pip_install --upgrade --force-reinstall --no-build-isolation "${INSTALL_DIR}"; then
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
if [[ "${SKIP_DEPS}" == "1" ]]; then
  echo "  Mode:   skip-deps"
fi
