"""
NetBox Loki plugin.

Display recent Loki logs in Device and VirtualMachine detail pages.
"""

import logging

from netbox.plugins import PluginConfig

__version__ = "1.2.0"

logger = logging.getLogger(__name__)


class LokiConfig(PluginConfig):
    """Plugin configuration for NetBox Loki integration."""

    name = "netbox_loki"
    verbose_name = "NetBox Loki Logs"
    description = "Display recent Loki logs in device, VM, and endpoint detail pages"
    version = __version__
    author = "-----"
    author_email = "---@gmail.com"
    base_url = "loki"
    min_version = "4.0.0"
    max_version = "5.99"

    # Required settings - plugin won't load without these
    required_settings = []

    # Default configuration values
    default_settings = {
        "loki_url": "http://localhost:3100",
        "loki_external_url": "",
        "loki_tenant": "docker",
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

    def ready(self):
        """Register endpoint view if netbox_endpoints is available."""
        super().ready()
        from . import widgets  # noqa: F401

        self._register_endpoint_views()

    def _register_endpoint_views(self):
        """Register Loki Logs tab for Endpoints if plugin is installed."""
        import sys

        # Quick check if netbox_endpoints is available
        if "netbox_endpoints" not in sys.modules:
            try:
                import importlib.util

                if importlib.util.find_spec("netbox_endpoints") is None:
                    logger.debug("netbox_endpoints not installed, skipping endpoint view registration")
                    return
            except Exception:
                logger.debug("netbox_endpoints not available, skipping endpoint view registration")
                return

        try:
            from django.shortcuts import render
            from netbox.views import generic
            from netbox_endpoints.models import Endpoint
            from utilities.views import ViewTab, register_model_view

            @register_model_view(Endpoint, name="loki_logs", path="logs")
            class EndpointLokiLogsView(generic.ObjectView):
                """Display Loki logs for an Endpoint with async loading."""

                queryset = Endpoint.objects.all()
                template_name = "netbox_loki/endpoint_logs_tab.html"

                tab = ViewTab(
                    label="Loki",
                    weight=9004,
                    permission="netbox_endpoints.view_endpoint",
                    hide_if_empty=False,
                )

                def get(self, request, pk):
                    endpoint = Endpoint.objects.get(pk=pk)
                    time_range = request.GET.get("range", "")
                    return render(
                        request,
                        self.template_name,
                        {
                            "object": endpoint,
                            "tab": self.tab,
                            "loading": True,
                            "time_range_param": time_range,
                        },
                    )

            logger.info("Registered Loki Logs tab for Endpoint model")
        except ImportError:
            logger.debug("netbox_endpoints not installed, skipping endpoint view registration")
        except Exception as e:
            logger.warning(f"Could not register endpoint views: {e}")


config = LokiConfig
