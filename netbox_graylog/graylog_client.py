"""
Loki API client.

The module name stays the same to preserve import compatibility with the
existing plugin package layout.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class LokiClient:
    """Client for querying Grafana Loki."""

    def __init__(self) -> None:
        self.config = settings.PLUGINS_CONFIG.get("netbox_graylog", {})
        self.base_url = self.config.get("loki_url", "http://localhost:3100").rstrip("/")
        self.timeout = self.config.get("timeout", 10)
        self.cache_timeout = self.config.get("cache_timeout", 60)
        self.verify_tls = self.config.get("verify_tls", True)

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "X-Requested-By": "NetBox-Loki-Plugin",
        }
        tenant = self.config.get("loki_tenant", "").strip()
        bearer = self.config.get("loki_bearer_token", "").strip()
        if tenant:
            headers["X-Scope-OrgID"] = tenant
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        return headers

    def _get_auth(self) -> tuple[str, str] | None:
        username = self.config.get("loki_username", "").strip()
        password = self.config.get("loki_password", "")
        if username:
            return (username, password)
        return None

    def _request(
        self,
        *,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._get_headers(),
            auth=self._get_auth(),
            timeout=self.timeout,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _ns_timestamp(value: datetime) -> str:
        return str(int(value.timestamp() * 1_000_000_000))

    @staticmethod
    def _format_timestamp(raw_value: str) -> str:
        try:
            as_int = int(raw_value)
            return datetime.fromtimestamp(as_int / 1_000_000_000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        except (TypeError, ValueError, OSError):
            return raw_value

    def _default_selector_parts(self) -> list[str]:
        parts: list[str] = []

        job = self.config.get("loki_job", "").strip()
        if job:
            parts.append(f'job="{self._escape_label_value(job)}"')

        extra_selector = self.config.get("stream_selector", "").strip()
        if extra_selector:
            parts.append(extra_selector)

        return parts

    @staticmethod
    def _escape_label_value(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _build_value_matcher(self, value: str) -> tuple[str, str]:
        if self.config.get("use_regex_matching", True):
            if "." in value:
                return "=~", self._escape_label_value(f"^{re.escape(value)}$")
            return "=~", self._escape_label_value(f"^{re.escape(value)}(?:\\..+)?$")
        return "=", self._escape_label_value(value)

    def _build_selector(self, *, label_name: str | None = None, value: str | None = None) -> str:
        selector_parts = self._default_selector_parts()
        effective_label = label_name or self.config.get("device_label", "routerboard")

        if value:
            operator, matcher = self._build_value_matcher(value)
            selector_parts.append(f'{effective_label}{operator}"{matcher}"')

        return "{" + ",".join(selector_parts) + "}"

    def search_logs(
        self,
        value: str | None = None,
        *,
        time_range: int | None = None,
        limit: int | None = None,
        label_name: str | None = None,
    ) -> dict[str, Any]:
        time_range = int(time_range or self.config.get("time_range", 3600))
        limit = int(limit or self.config.get("log_limit", 100))
        selector = self._build_selector(label_name=label_name, value=value)

        cache_key = f"loki_logs::{selector}::{time_range}::{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        end = datetime.now(timezone.utc)
        start = end - timedelta(seconds=time_range)
        query = selector

        try:
            payload = self._request(
                endpoint="/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": self._ns_timestamp(start),
                    "end": self._ns_timestamp(end),
                    "limit": limit,
                    "direction": "backward",
                },
            )
            result = self._parse_log_response(payload, query=query, time_range=time_range)
            cache.set(cache_key, result, self.cache_timeout)
            return result
        except requests.RequestException as exc:
            logger.warning("Loki request failed for query %s: %s", query, exc)
            return {"error": str(exc), "messages": [], "query": query, "time_range": time_range}

    def _parse_log_response(self, payload: dict[str, Any], *, query: str, time_range: int) -> dict[str, Any]:
        messages: list[dict[str, Any]] = []
        data = payload.get("data", {})

        for stream in data.get("result", []):
            labels = stream.get("stream", {})
            for timestamp, line in stream.get("values", []):
                messages.append(
                    {
                        "message": {
                            "timestamp": timestamp,
                            "timestamp_display": self._format_timestamp(timestamp),
                            "message": line,
                            "source": self._derive_source(labels),
                            "job": labels.get("job", ""),
                            "severity": labels.get("severity", labels.get("level", "")),
                            "labels": labels,
                        }
                    }
                )

        messages.sort(key=lambda item: item["message"]["timestamp"], reverse=True)

        return {
            "messages": messages,
            "total_results": len(messages),
            "query": query,
            "time_range": time_range,
        }

    def _derive_source(self, labels: dict[str, str]) -> str:
        configured_label = self.config.get("device_label", "routerboard")
        for key in (configured_label, "host", "hostname", "instance", "source"):
            value = labels.get(key)
            if value:
                return value
        return ""

    @staticmethod
    def _primary_ip_value(primary_ip: Any) -> str | None:
        if not primary_ip:
            return None
        address = getattr(primary_ip, "address", None)
        if not address:
            return None
        return str(address).split("/")[0]

    def _search_with_fallback(
        self,
        *,
        name: str,
        time_range: int | None,
        fallback_ip: str | None = None,
        label_name: str | None = None,
    ) -> dict[str, Any]:
        result = self.search_logs(name, time_range=time_range, label_name=label_name)
        result["search_type"] = "name"

        if result.get("messages") or not self.config.get("fallback_to_ip", True) or not fallback_ip:
            return result

        fallback = self.search_logs(fallback_ip, time_range=time_range, label_name=label_name)
        fallback["search_type"] = "ip"
        return fallback

    def get_logs_for_device(self, device: Any, *, time_range: int | None = None) -> dict[str, Any]:
        hostname = device.virtual_chassis.name if getattr(device, "virtual_chassis", None) else device.name
        fallback_ip = self._primary_ip_value(getattr(device, "primary_ip", None))
        result = self._search_with_fallback(name=hostname, time_range=time_range, fallback_ip=fallback_ip)
        result["device_name"] = device.name
        return result

    def get_logs_for_vm(self, vm: Any, *, time_range: int | None = None) -> dict[str, Any]:
        fallback_ip = self._primary_ip_value(getattr(vm, "primary_ip", None))
        result = self._search_with_fallback(name=vm.name, time_range=time_range, fallback_ip=fallback_ip)
        result["vm_name"] = vm.name
        return result

    def get_logs_for_endpoint(self, endpoint: Any, *, time_range: int | None = None) -> dict[str, Any]:
        search_value = endpoint.name or str(endpoint.mac_address)
        fallback_ip = self._primary_ip_value(getattr(endpoint, "primary_ip", None))
        result = self._search_with_fallback(name=search_value, time_range=time_range, fallback_ip=fallback_ip)
        result["endpoint_name"] = search_value
        return result

    def _instant_scalar_query(self, query: str) -> int:
        payload = self._request(
            endpoint="/loki/api/v1/query",
            params={
                "query": query,
                "time": self._ns_timestamp(datetime.now(timezone.utc)),
            },
        )
        result = payload.get("data", {}).get("result", [])
        if not result:
            return 0

        value = result[0].get("value", [None, "0"])
        try:
            return int(float(value[1]))
        except (TypeError, ValueError, IndexError):
            return 0

    @staticmethod
    def _duration_expr(time_range: int) -> str:
        if time_range % 86400 == 0:
            return f"{time_range // 86400}d"
        if time_range % 3600 == 0:
            return f"{time_range // 3600}h"
        if time_range % 60 == 0:
            return f"{time_range // 60}m"
        return f"{time_range}s"

    def get_log_summary(self, time_range: int = 3600, cache_timeout: int = 120) -> dict[str, Any]:
        cache_key = f"loki_log_summary::{time_range}"
        cached = cache.get(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

        selector = self._build_selector()
        range_expr = self._duration_expr(time_range)

        try:
            total = self._instant_scalar_query(f"sum(count_over_time({selector}[{range_expr}]))")
            errors = self._instant_scalar_query(
                f'sum(count_over_time({selector} |~ "(?i)error|err|critical|fatal"[{range_expr}]))'
            )
            warnings = self._instant_scalar_query(
                f'sum(count_over_time({selector} |~ "(?i)warn|warning"[{range_expr}]))'
            )
        except requests.RequestException as exc:
            logger.warning("Loki summary query failed: %s", exc)
            return {"error": str(exc)}

        summary = {
            "total": total,
            "errors": errors,
            "warnings": warnings,
            "cached": False,
        }
        cache.set(cache_key, summary, cache_timeout)
        return summary


GraylogClient = LokiClient

_client: LokiClient | None = None


def get_client() -> LokiClient:
    """Get or create the Loki client singleton."""
    global _client
    if _client is None:
        _client = LokiClient()
    return _client
