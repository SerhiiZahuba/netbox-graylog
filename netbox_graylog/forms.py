"""
Forms for NetBox Loki Plugin settings.
"""

from django import forms


class GraylogSettingsForm(forms.Form):
    """Form for configuring Loki plugin settings."""

    graylog_url = forms.URLField(
        label="Loki URL",
        help_text="Base URL for Loki API (e.g., http://192.168.110.117:8080)",
        required=True,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "http://192.168.110.117:8080",
            }
        ),
    )

    loki_tenant = forms.CharField(
        label="Loki Tenant",
        help_text="Value for X-Scope-OrgID header",
        required=True,
        initial="docker",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "docker",
            }
        ),
    )

    loki_job = forms.CharField(
        label="Loki Job Label",
        help_text='Loki job label, for example: syslog',
        required=True,
        initial="syslog",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "syslog",
            }
        ),
    )

    routerboard_label = forms.CharField(
        label="Routerboard Label",
        help_text='Loki label used for device name, for example: routerboard',
        required=True,
        initial="routerboard",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "routerboard",
            }
        ),
    )

    log_limit = forms.IntegerField(
        label="Log Limit",
        help_text="Maximum number of logs to display per request",
        required=False,
        initial=100,
        min_value=10,
        max_value=500,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    time_range = forms.ChoiceField(
        label="Default Time Range",
        help_text="Default time range for log queries",
        choices=[
            (300, "5 minutes"),
            (900, "15 minutes"),
            (3600, "1 hour"),
            (14400, "4 hours"),
            (86400, "24 hours"),
            (604800, "7 days"),
        ],
        initial=86400,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    timeout = forms.IntegerField(
        label="API Timeout",
        help_text="Timeout for Loki API requests (seconds)",
        required=False,
        initial=10,
        min_value=5,
        max_value=60,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    cache_timeout = forms.IntegerField(
        label="Cache Timeout",
        help_text="How long to cache API responses (seconds)",
        required=False,
        initial=60,
        min_value=0,
        max_value=300,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )