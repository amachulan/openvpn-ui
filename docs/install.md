# Install vpnctl

## Prerequisites

1. Linux VPS (Ubuntu/Debian).
2. OpenVPN via [angristan/openvpn-install](https://github.com/angristan/openvpn-install).
3. Python 3.10+.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/amachulan/vpnctl/main/scripts/install.sh | sudo bash
```

That is enough: package, config, systemd enable/start.

Open `http://SERVER_IP:8080/`, paste the token printed at the end (also in `/etc/vpnctl/config.yaml`).

If the one-liner fails, use the local copy:

```bash
sudo git -C /opt/vpnctl pull --ff-only
sudo bash /opt/vpnctl/scripts/install.sh --from-local
```

### PyPI blocked / timeouts

`install.sh` auto-probes mirrors. Force one if needed:

```bash
curl -fsSL https://raw.githubusercontent.com/amachulan/vpnctl/main/scripts/install.sh \
  | sudo env VPNCTL_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple bash
```

## Config

File: `/etc/vpnctl/config.yaml`

Defaults:

- `api.host: 0.0.0.0` (reachable over VPN / LAN / public IP)
- `api.port: 8080`
- strong `api.token` generated on install

Optional hardening (VPN clients only):

```yaml
api:
  allow_from_vpn: true
  allow_from:
    - 127.0.0.1/32
```

Then: `sudo systemctl restart vpnctl`.

Optional mail / Telegram delivery — see comments in the config file.

## Verify

```bash
systemctl status vpnctl --no-pager
vpnctl health
```
