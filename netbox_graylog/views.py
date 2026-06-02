"""
Views for the NetBox Loki plugin.

Registers custom tabs on Device and VirtualMachine detail views and provides
an informational settings UI.
"""

from __future__ import annotations

import logging
from typing import Any

from dcim.models import Device
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views import View
from netbox.views import generic
from utilities.views import ViewTab, register_model_view
from virtualization.models import VirtualMachine

from .forms import GraylogSettingsForm
from .graylog_client import get_client

logger = logging.getLogger(__name__)

try:
    from netbox_endpoints.models import Endpoint

    ENDPOINTS_PLUGIN_INSTALLED = True
except ImportError:
    ENDPOINTS_PLUGIN_INSTALLED = False


def _parse_time_range(raw_value: str | None) -> int | None:
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def _external_log_url() -> str:
    config = settings.PLUGINS_CONFIG.get("netbox_graylog", {})
    return (config.get("loki_external_url") or config.get("loki_url") or "").rstrip("/")


def _render_log_response(
    request,
    *,
    obj: Any,
    logs_data: dict[str, Any],
    default_search_type: str = "name",
) -> HttpResponse:
    return HttpResponse(
        render_to_string(
            "netbox_graylog/logs_tab_content.html",
            {
                "object": obj,
                "logs": logs_data.get("messages", []),
                "error": logs_data.get("error"),
                "total_results": logs_data.get("total_results", 0),
                "query": logs_data.get("query", ""),
                "time_range": logs_data.get("time_range", 3600),
                "search_type": logs_data.get("search_type", default_search_type),
                "external_log_url": _external_log_url(),
            },
            request=request,
        )
    )


@register_model_view(Device, name="graylog_logs", path="logs")
class DeviceGraylogLogsView(generic.ObjectView):
    """Display Loki logs for a Device with async loading."""

    queryset = Device.objects.all()
    template_name = "netbox_graylog/device_logs_tab.html"

    tab = ViewTab(
        label="Loki",
        weight=9004,
        permission="dcim.view_device",
        hide_if_empty=False,
    )

    def get(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        time_range = request.GET.get("range", "")

        return render(
            request,
            self.template_name,
            {
                "object": device,
                "tab": self.tab,
                "loading": True,
                "time_range_param": time_range,
            },
        )


class DeviceGraylogContentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX endpoint that returns Loki content for async loading."""

    permission_required = "dcim.view_device"

    def get(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        time_range = _parse_time_range(request.GET.get("range"))
        logs_data = get_client().get_logs_for_device(device, time_range=time_range)
        return _render_log_response(request, obj=device, logs_data=logs_data)


@register_model_view(VirtualMachine, name="graylog_logs", path="logs")
class VirtualMachineGraylogLogsView(generic.ObjectView):
    """Display Loki logs for a VirtualMachine with async loading."""

    queryset = VirtualMachine.objects.all()
    template_name = "netbox_graylog/vm_logs_tab.html"

    tab = ViewTab(
        label="Loki",
        weight=9004,
        permission="virtualization.view_virtualmachine",
        hide_if_empty=False,
    )

    def get(self, request, pk):
        vm = get_object_or_404(VirtualMachine, pk=pk)
        time_range = request.GET.get("range", "")

        return render(
            request,
            self.template_name,
            {
                "object": vm,
                "tab": self.tab,
                "loading": True,
                "time_range_param": time_range,
            },
        )


class VMGraylogContentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX endpoint that returns Loki content for VM async loading."""

    permission_required = "virtualization.view_virtualmachine"

    def get(self, request, pk):
        vm = get_object_or_404(VirtualMachine, pk=pk)
        time_range = _parse_time_range(request.GET.get("range"))
        logs_data = get_client().get_logs_for_vm(vm, time_range=time_range)
        return _render_log_response(request, obj=vm, logs_data=logs_data)


class GraylogSettingsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Read-only view for displaying Loki plugin settings."""

    permission_required = "netbox_graylog.configure_graylog"
    template_name = "netbox_graylog/settings.html"

    def get_current_config(self) -> dict[str, Any]:
        return settings.PLUGINS_CONFIG.get("netbox_graylog", {})

    def get(self, request):
        form = GraylogSettingsForm(initial=self.get_current_config())
        return render(request, self.template_name, {"form": form, "config": self.get_current_config()})

    def post(self, request):
        form = GraylogSettingsForm(request.POST)
        if form.is_valid():
            messages.warning(
                request,
                "Plugin settings remain read-only at runtime. Update PLUGINS_CONFIG in NetBox and reload the service.",
            )
        else:
            messages.error(request, "The provided Loki settings are invalid.")

        return render(request, self.template_name, {"form": form, "config": self.get_current_config()})


class TestConnectionView(View):
    """Test connection to the Loki API."""

    def post(self, request):
        result = get_client().search_logs(time_range=60, limit=1)
        if result.get("error"):
            return JsonResponse({"success": False, "error": result["error"]}, status=400)

        return JsonResponse(
            {
                "success": True,
                "message": f"Connected successfully. Found {result.get('total_results', 0)} log lines in the last minute.",
            }
        )


if ENDPOINTS_PLUGIN_INSTALLED:

    class EndpointGraylogContentView(LoginRequiredMixin, PermissionRequiredMixin, View):
        """HTMX endpoint that returns Loki content for endpoint async loading."""

        permission_required = "netbox_endpoints.view_endpoint"

        def get(self, request, pk):
            endpoint = get_object_or_404(Endpoint, pk=pk)
            time_range = _parse_time_range(request.GET.get("range"))
            logs_data = get_client().get_logs_for_endpoint(endpoint, time_range=time_range)
            return _render_log_response(request, obj=endpoint, logs_data=logs_data)
