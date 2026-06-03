from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LokiPermission",
            fields=[],
            options={
                "managed": False,
                "default_permissions": (),
                "permissions": (("configure_loki", "Can configure Loki plugin settings"),),
            },
        ),
    ]