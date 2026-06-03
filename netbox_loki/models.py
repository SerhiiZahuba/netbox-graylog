from django.db import models


class Loki(models.Model):
    """Unmanaged model to register custom permissions for the log plugin."""

    # Excluded from NetBox's /core/system/ object-count loop; the model has no DB table.
    _netbox_private = True

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("configure_loki", "Can configure Loki plugin settings"),)
