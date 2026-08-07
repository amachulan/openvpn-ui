# Install openvpn-ui

## Prerequisites

1. Linux VPS (Ubuntu/Debian).
2. OpenVPN via [angristan/openvpn-install](https://github.com/angristan/openvpn-install).
3. Python 3.10+.

## Install / upgrade (same one-liner)

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/openvpn-ui/main/scripts/install.sh?$(date +%s)" | sudo bash
```

Re-run anytime to pull latest code, reinstall the package, and restart the service.  
`/etc/openvpn-ui/config.yaml` (and your API token) are **kept**.

### Fast upgrade (skip apt / mirror probes)

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/openvpn-ui/main/scripts/install.sh?$(date +%s)" \
  | sudo env OPENVPN_UI_SKIP_DEPS=1 bash
```

Or locally: `sudo bash /opt/openvpn-ui/scripts/install.sh --from-local --skip-deps`

After it finishes, open `http://SERVER_IP:8080/` and paste the printed token.

### PyPI blocked

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/openvpn-ui/main/scripts/install.sh?$(date +%s)" \
  | sudo env OPENVPN_UI_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple bash
```

## Config

File: `/etc/openvpn-ui/config.yaml`

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

Then the next one-liner restart will apply it, or: `sudo systemctl restart openvpn-ui`.

## OpenVPN server admin (UI)

The **Server** tab edits `/etc/openvpn/server/server.conf` (with backups under `/var/lib/openvpn-ui/backups/`) and can restart the OpenVPN unit (default `openvpn-server@server`).

openvpn-ui runs as root via systemd today, so `systemctl restart openvpn-server@server` works. Override the unit name with:

```yaml
openvpn:
  service: openvpn-server@server
```

If a save breaks the VPN, restore from the Server → Backups list, or:

```bash
sudo cp /var/lib/openvpn-ui/backups/server.conf.TIMESTAMP /etc/openvpn/server/server.conf
sudo systemctl restart openvpn-server@server
```

## Verify

```bash
systemctl status openvpn-ui --no-pager
openvpn-ui health
```
