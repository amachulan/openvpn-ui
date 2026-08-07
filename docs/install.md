# Install vpnctl

## Prerequisites

1. Linux VPS (Ubuntu/Debian).
2. OpenVPN via [angristan/openvpn-install](https://github.com/angristan/openvpn-install).
3. Python 3.10+.

## Install / upgrade (same one-liner)

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/vpnctl/main/scripts/install.sh?$(date +%s)" | sudo bash
```

Re-run anytime to pull latest code, reinstall the package, and restart the service.  
`/etc/vpnctl/config.yaml` (and your API token) are **kept**.

After it finishes, open `http://SERVER_IP:8080/` and paste the printed token.

### PyPI blocked

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/vpnctl/main/scripts/install.sh?$(date +%s)" \
  | sudo env VPNCTL_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple bash
```

## Config

File: `/etc/vpnctl/config.yaml`

Defaults:

- `api.host: 0.0.0.0`
- `api.port: 8080`
- `api.token` generated once on first install

Optional hardening (VPN clients only):

```yaml
api:
  allow_from_vpn: true
  allow_from:
    - 127.0.0.1/32
```

Then the next one-liner restart will apply it, or: `sudo systemctl restart vpnctl`.

## Verify

```bash
systemctl status vpnctl --no-pager
vpnctl health
```
