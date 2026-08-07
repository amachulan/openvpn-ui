# vpnctl

Web UI and API for managing a self-hosted **OpenVPN Community** server.

Built to sit on top of servers installed with [angristan/openvpn-install](https://github.com/angristan/openvpn-install) (or a compatible Easy-RSA layout).

## Features (MVP + v0.2)

- List certificates from Easy-RSA `index.txt`
- Issue client (`build-client-full`) and build inline `.ovpn`
- Revoke + publish CRL
- Download profile
- Online sessions (status log / management) + disconnect
- Token-auth API (binds `0.0.0.0` by default)
- Labels / notes, audit log, expiry warnings
- Optional email / Telegram delivery of `.ovpn`

## Quick start

1. Install OpenVPN with angristan.
2. Install or upgrade vpnctl (same command every time):

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/vpnctl/main/scripts/install.sh?$(date +%s)" | sudo bash
```

Fast upgrades (skip apt + mirror checks):

```bash
curl -fsSL "https://raw.githubusercontent.com/amachulan/vpnctl/main/scripts/install.sh?$(date +%s)" | sudo env VPNCTL_SKIP_DEPS=1 bash
```

3. Open `http://SERVER_IP:8080/`, paste the API token printed by the installer.

Config and token in `/etc/vpnctl/config.yaml` survive upgrades.

See [docs/install.md](docs/install.md).

## Development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
VPNCTL_CONFIG=./config/vpnctl.yaml.example vpnctl serve --host 127.0.0.1 --port 8080
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
| GET | `/api/v1/clients/{cn}/ovpn` | Download `.ovpn` |
| POST | `/api/v1/clients/{cn}/deliver` | Email/Telegram delivery |
| GET | `/api/v1/sessions` | Online clients |
| POST | `/api/v1/sessions/disconnect` | Kick session |
| GET | `/api/v1/expiry` | Certs nearing expiry |
| GET | `/api/v1/audit` | Audit events |

Auth: `Authorization: Bearer <token>` or `X-API-Token`.

## Roadmap

| Phase | Status | Scope |
|-------|--------|--------|
| Skeleton | done | package, config, health, UI shell |
| MVP | done | issue / revoke / download / sessions |
| v0.2 | done | labels, audit, expiry, mail/telegram |
| Later | planned | groups + push routes, self-service link, OIDC admin, metrics |
| Optional | maybe | network segmentation module |

## License

MIT — see [LICENSE](LICENSE).
