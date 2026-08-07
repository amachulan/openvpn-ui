# openvpn-ui

Web UI and API for administering a self-hosted **OpenVPN Community** server (clients **and** `server.conf`).

Built to sit on top of servers installed with [angristan/openvpn-install](https://github.com/angristan/openvpn-install) (or a compatible Easy-RSA layout).

## Features

- List certificates from Easy-RSA `index.txt`
- Issue / renew / revoke clients and build inline `.ovpn`
- Online sessions (status log / management) + disconnect
- **Server admin:** structured settings (port, proto, DNS, routes, cipher, …), raw `server.conf`, backups/restore, OpenVPN restart
- Token-auth API (binds `0.0.0.0` by default)
- Labels / notes, audit log, expiry warnings
- Optional email / Telegram delivery of `.ovpn` (Settings tab)

## Quick start

1. Install OpenVPN with angristan.
2. Install or upgrade openvpn-ui (same command every time):

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/openvpn-ui/main/scripts/install.sh?$(date +%s)" | sudo bash
```

Fast upgrades (skip apt + mirror checks):

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/openvpn-ui/main/scripts/install.sh?$(date +%s)" | sudo env OPENVPN_UI_SKIP_DEPS=1 bash
```

3. Open `http://SERVER_IP:8080/`, paste the API token printed by the installer.

Config and token in `/etc/openvpn-ui/config.yaml` survive upgrades.

See [docs/install.md](docs/install.md).

## Development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
OPENVPN_UI_CONFIG=./config/openvpn-ui.yaml.example openvpn-ui serve --host 127.0.0.1 --port 8080
```

Copy and edit the example config before real use; set a strong `api.token`.

Default bind is `0.0.0.0:8080`. For VPN-only access set `api.allow_from_vpn: true` (see [docs/install.md](docs/install.md)).

## API (auth required except health)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Paths / readiness |
| GET | `/api/v1/clients` | Certificates + meta |
| POST | `/api/v1/clients` | Issue client |
| PATCH | `/api/v1/clients/{cn}` | Update label/notes/email |
| POST | `/api/v1/clients/{cn}/revoke` | Revoke |
| POST | `/api/v1/clients/{cn}/renew` | Renew certificate |
| GET | `/api/v1/clients/{cn}/ovpn` | Download `.ovpn` |
| POST | `/api/v1/clients/{cn}/deliver` | Email/Telegram delivery |
| GET | `/api/v1/sessions` | Online clients |
| POST | `/api/v1/sessions/disconnect` | Kick session |
| GET | `/api/v1/server` | Structured server settings + service status |
| PUT | `/api/v1/server` | Patch server.conf (backed up) |
| GET | `/api/v1/server/conf` | Raw server.conf |
| PUT | `/api/v1/server/conf` | Replace raw server.conf |
| GET | `/api/v1/server/backups` | List conf backups |
| POST | `/api/v1/server/backups/{id}/restore` | Restore backup |
| POST | `/api/v1/server/restart` | Restart OpenVPN unit |
| GET | `/api/v1/expiry` | Certs nearing expiry |
| GET | `/api/v1/audit` | Audit events |
| GET | `/api/v1/settings/notify` | Mail/Telegram settings (secrets redacted) |
| PUT | `/api/v1/settings/notify` | Update mail/Telegram (persists to config.yaml) |

Auth: `Authorization: Bearer <token>` or `X-API-Token`.

## Roadmap

| Phase | Status | Scope |
|-------|--------|--------|
| Skeleton | done | package, config, health, UI shell |
| MVP | done | issue / revoke / download / sessions |
| v0.2 | done | labels, audit, expiry, mail/telegram |
| v0.2.0 server | done | server.conf admin, backups, restart, renew |
| Later | planned | groups + CCD push routes, self-service link, OIDC admin, metrics |
| Optional | maybe | network segmentation module |

## License

MIT — see [LICENSE](LICENSE).
