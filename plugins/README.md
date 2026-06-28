# Collection Plugins — `bodsch.influx`

All InfluxDB configuration is performed through the HTTP API (InfluxDB 2
`/api/v2`, InfluxDB 3 `/api/v3`). No module shells out to a CLI and no module
relies on `subprocess`. Shared HTTP/transport logic lives in `module_utils/`.

## modules

### InfluxDB 2

| Module | Purpose |
| --- | --- |
| `bodsch.influx.influxdb2_ping` | Health check via `/health` (never fails; use with `retries`/`until`). |
| `bodsch.influx.influxdb2_setup` | Initial onboarding (`/api/v2/setup`); idempotent via the `allowed` flag. |
| `bodsch.influx.influxdb2_organizations` | Manage organizations (whole set at once, no `loop`). |
| `bodsch.influx.influxdb2_users` | Manage users + org membership (member/owner). |
| `bodsch.influx.influxdb2_buckets` | Manage buckets incl. retention (`0`, `30m`, `1d`, …). |
| `bodsch.influx.influxdb2_auth` | Manage authorizations (API tokens). |

### InfluxDB 3

| Module | Purpose |
| --- | --- |
| `bodsch.influx.influxdb3_ping` | Health check via `/health`. |
| `bodsch.influx.influxdb3_token` | Create/regenerate the operator token; optional `token_file` cache for idempotency. |
| `bodsch.influx.influxdb3_database` | Manage databases (`/api/v3/configure/database`). |

### shared

| Module | Purpose |
| --- | --- |
| `bodsch.influx.influx_download_data` | Resolve version, artifact name, URL and SHA256 for v2/v3 Linux tarballs. |

All resource modules accept the full data set as a dictionary and iterate
internally; each returns a per-item result list of
`{name: {changed, failed, state}}`, aggregated through
`bodsch.core ... module_results.results`. Every module supports check mode.

## module_utils

| Module | Contents |
| --- | --- |
| `influx_http` | `InfluxHTTP` (JSON-over-HTTP client around `fetch_url`) and `InfluxHTTPError`. |
| `influxdb2` | `InfluxDB2Client` (resource operations) plus `parse_duration`, `bucket_retention_seconds`. |
| `influxdb3` | `InfluxDB3Client` (admin token, databases, health). |
| `influx_downloads` | `InfluxDownloads` resolver, `DownloadInfo`, `DownloadNotFoundError`. |

```python
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb2 import InfluxDB2Client
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb3 import InfluxDB3Client
```

## filter

| Filter | Signature | Purpose |
| --- | --- | --- |
| `influx_binaries` | `influx_binaries(find_results)` | Map `find` results to `{basename: path}`. |
| `influxdb_fix_release` | `influxdb_fix_release(data, influxdb_version, version=None)` | Switch the v2 artifact separators for newer releases. |
| `influxdb_fix_binary` | `influxdb_fix_binary(data, influxdb_version, influxdb_type="")` | Build the server/client artifact base name. |
| `influxdb_update_release` | `influxdb_update_release(data, core_version, client_version)` | Populate download URLs/files/binaries. |
| `influxdb_bind` | `influxdb_bind(data, core_version)` | Build the `http://host:port` bind URL. |
| `telegraf_checksum` | `telegraf_checksum(data, os, arch)` | Pick the checksum for an OS/arch tarball. |
| `telegraf_clean_list` | `telegraf_clean_list(data)` | Drop Telegraf plugin entries without a config. |
| `telegraf_input_value` | `telegraf_input_value(var)` | Render a value as a TOML literal (`is_set, value`). |

## Testing

Unit tests live in `tests/unit/` and run with plain `pytest` (a bootstrap
`conftest.py` makes the collection importable) or with `ansible-test units`:

```bash
pytest tests/unit -q
ansible-test sanity --test validate-modules --test import --test pep8 plugins/
```
