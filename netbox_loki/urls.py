"""
URL routing for the NetBox Loki plugin.
"""

from django.urls import path

from . import views
from .views import ENDPOINTS_PLUGIN_INSTALLED

urlpatterns = [
    path("settings/", views.LokiSettingsView.as_view(), name="settings"),
    path("test-connection/", views.TestConnectionView.as_view(), name="test_connection"),
    path("device/<int:pk>/content/", views.DeviceLokiContentView.as_view(), name="device_content"),
    path("vm/<int:pk>/content/", views.VMLokiContentView.as_view(), name="vm_content"),
]

# Add endpoint URLs if netbox_endpoints is installed
if ENDPOINTS_PLUGIN_INSTALLED:
    urlpatterns.append(
        path("endpoint/<int:pk>/content/", views.EndpointLokiContentView.as_view(), name="endpoint_content"),
    )
