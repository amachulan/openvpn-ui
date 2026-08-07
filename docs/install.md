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

The **Server** tab shows **UDP** and **TCP** instance cards. The primary instance is your existing `/etc/openvpn/server/server.conf` (and `openvpn-server@server`). Enabling the secondary clones that conf to `server-tcp.conf` or `server-udp.conf` (opposite proto), rewrites status/management/ipp paths, keeps shared PKI/CCD/`server` subnet, then runs `systemctl enable --now openvpn-server@server-tcp` (or `@server-udp`).

Clients get separate profiles: `{cn}-udp.ovpn` and `{cn}-tcp.ovpn`. Do not connect both at once with the same CN unless `duplicate-cn` is on. openvpn-ui does **not** open the firewall for the secondary port — allow it yourself (e.g. TCP 443).

Backups live under `/var/lib/openvpn-ui/backups/` (prefixed by conf basename).

Example `openvpn.instances` (written automatically when you enable/disable in the UI):

```yaml
openvpn:
  service: ""   # legacy primary override
  instances:
    udp:
      enabled: true
      conf: /etc/openvpn/server/server.conf
      service: openvpn-server@server
      port: 1194
      primary: true
    tcp:
      enabled: true
      conf: /etc/openvpn/server/server-tcp.conf
      service: openvpn-server@server-tcp
      port: 443
      primary: false
```

If a save breaks the VPN, restore from the instance Backups list, or:

```bash
sudo cp /var/lib/openvpn-ui/backups/server.conf.TIMESTAMP /etc/openvpn/server/server.conf
sudo systemctl restart openvpn-server@server
```

## Verify

```bash
systemctl status openvpn-ui --no-pager
openvpn-ui health
```
