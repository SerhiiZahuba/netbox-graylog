"""
Navigation menu items for the NetBox Loki plugin.
"""

from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="Loki",
    groups=(
        (
            "Settings",
            (
                PluginMenuItem(
                    link="plugins:netbox_loki:settings",
                    link_text="Configuration",
                    permissions=["netbox_loki.configure_loki"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-file-document-outline",
)
