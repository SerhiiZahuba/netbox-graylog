# NetBox Loki Logs Plugin


This is a fork from https://github.com/sieteunoseis/netbox-graylog


<img src="docs/icon.png" alt="NetBox Loki Logs Plugin" width="100" align="right">

A NetBox plugin that displays recent Loki logs on Device, VirtualMachine, and optional Endpoint detail pages.

![NetBox Version](https://img.shields.io/badge/NetBox-4.0+-blue)
![Python Version](https://img.shields.io/badge/Python-3.10+-green)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## What Changed

This fork replaces the unfinished Graylog integration with a Loki-based implementation:

- Queries Loki via `/loki/api/v1/query_range`
- Supports optional `X-Scope-OrgID`, bearer token, and basic auth
- Matches devices by a configurable Loki label such as `routerboard`, `host`, or `hostname`
- Can fall back to a NetBox primary IP when hostname lookup returns no results
- Provides a Loki summary dashboard widget based on LogQL aggregations

## Features

- **Logs tab** on Device and VirtualMachine pages
- **Optional Endpoint support** when `netbox_endpoints` is installed
- **Time range selector** for 5m, 15m, 1h, 4h, 24h, and 7d
- **Caching** to reduce API load on Loki
- **Connection test** from the plugin settings page
- **Shortname/FQDN matching** for label-based hostname lookups

## Requirements

- NetBox 4.0 or higher
- Python 3.10+
- Grafana Loki reachable from the NetBox instance

## Installation

```bash
git clone https://github.com/SerhiiZahuba/netbox-graylog.git
cd netbox-graylog
pip install -e .
```

## Configuration

Add the plugin to NetBox:

```python
PLUGINS = [
    "netbox_graylog",
]

PLUGINS_CONFIG = {
    "netbox_graylog": {
        "loki_url": "http://loki:3100",
        "loki_external_url": "https://grafana.example.com/explore",
        "loki_tenant": "loki_tenant",
        "loki_username": "",
        "loki_password": "",
        "loki_bearer_token": "",
        "loki_job": "syslog",
        "device_label": "routerboard",
        "stream_selector": "",
        "log_limit": 100,
        "time_range": 3600,
        "timeout": 10,
        "cache_timeout": 60,
        "verify_tls": True,
        "use_regex_matching": True,
        "fallback_to_ip": True,
    }
}
```

## Loki Query Model

The plugin builds LogQL stream selectors like:

```logql
{job="syslog",routerboard=~"^edge-sw01(?:\\..+)?$"}
```

You can further narrow the stream by setting `stream_selector`, for example:

```python
"stream_selector": 'site="kyiv",env="prod"'
```

## Notes

- `device_label` should point to the Loki label that contains the NetBox object name.
- If your labels contain FQDNs while NetBox stores short names, leave `use_regex_matching=True`.
- `loki_external_url` is only used for opening the log platform from the UI; API calls still use `loki_url`.
- Authorization in Loki is commonly provided by a reverse proxy or managed service. This plugin supports optional bearer token and basic auth for that case.

## Troubleshooting

### No logs appear

- Verify the object name in NetBox matches the configured Loki label value.
- Confirm `device_label` points to the correct Loki label.
- Check `stream_selector` and `loki_job` are not overly restrictive.
- Enable `fallback_to_ip` if your logs are labeled by IP rather than hostname.

### Connection test fails

- Verify `loki_url` is reachable from the NetBox host or container.
- If Loki uses multi-tenancy, set `loki_tenant`.
- If TLS is self-signed, set `verify_tls=False`.
- If access is proxied, configure `loki_bearer_token` or `loki_username` / `loki_password`.

## Development

```bash
pip install -e ".[dev]"
```

## License

Apache License 2.0 - see [LICENSE](LICENSE).

## Reference

- [Grafana Loki HTTP API](https://grafana.com/docs/loki/latest/api/)
