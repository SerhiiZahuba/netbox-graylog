"""
Forms for NetBox Loki plugin settings.
"""

from django import forms


class LokiSettingsForm(forms.Form):
    """Form for displaying Loki plugin settings."""

    loki_url = forms.URLField(
        label="Loki URL",
        help_text="Base URL for the Loki HTTP API, for example: http://loki:3100",
        required=True,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "http://loki:3100",
            }
        ),
    )

    loki_external_url = forms.URLField(
        label="External URL",
        help_text="Optional browser URL for opening Loki or Grafana from the NetBox UI.",
        required=False,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://grafana.example.com/explore",
            }
        ),
    )

    loki_tenant = forms.CharField(
        label="Tenant Header",
        help_text="Optional value for the X-Scope-OrgID header when Loki multi-tenancy is enabled.",
        required=False,
        initial="docker",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "docker",
            }
        ),
    )

    loki_username = forms.CharField(
        label="Username",
        help_text="Optional basic-auth username used by a reverse proxy or managed Loki.",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    loki_password = forms.CharField(
        label="Password",
        help_text="Optional basic-auth password.",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}, render_value=True),
    )

    loki_bearer_token = forms.CharField(
        label="Bearer Token",
        help_text="Optional bearer token if your Loki endpoint is protected by token auth.",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}, render_value=True),
    )

    loki_job = forms.CharField(
        label="Job Label Value",
        help_text='Optional value for the standard Loki label `job`, for example: `syslog`.',
        required=False,
        initial="syslog",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "syslog",
            }
        ),
    )

    device_label = forms.CharField(
        label="Device Label",
        help_text='Loki label that stores the device or VM name, for example: `routerboard`, `host`, or `hostname`.',
        required=True,
        initial="routerboard",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "routerboard",
            }
        ),
    )

    stream_selector = forms.CharField(
        label="Extra Stream Selector",
        help_text='Optional extra Loki label selector fragment without braces, for example: `site="kyiv",env="prod"`.',
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": 'site="kyiv",env="prod"',
            }
        ),
    )

    log_limit = forms.IntegerField(
        label="Log Limit",
        help_text="Maximum number of log lines to display per request.",
        required=False,
        initial=100,
        min_value=10,
        max_value=500,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    time_range = forms.ChoiceField(
        label="Default Time Range",
        help_text="Default time range for log queries.",
        choices=[
            (300, "5 minutes"),
            (900, "15 minutes"),
            (3600, "1 hour"),
            (14400, "4 hours"),
            (86400, "24 hours"),
            (604800, "7 days"),
        ],
        initial=3600,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    timeout = forms.IntegerField(
        label="API Timeout",
        help_text="Timeout for Loki API requests in seconds.",
        required=False,
        initial=10,
        min_value=5,
        max_value=60,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    cache_timeout = forms.IntegerField(
        label="Cache Timeout",
        help_text="How long to cache API responses in seconds.",
        required=False,
        initial=60,
        min_value=0,
        max_value=300,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    verify_tls = forms.BooleanField(
        label="Verify TLS Certificates",
        help_text="Disable only if your Loki endpoint uses a self-signed certificate.",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    use_regex_matching = forms.BooleanField(
        label="Allow Shortname/FQDN Matching",
        help_text="Match `router1` against both `router1` and `router1.example.com` in Loki labels.",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    fallback_to_ip = forms.BooleanField(
        label="Fallback To Primary IP",
        help_text="If hostname lookup returns no logs, try the primary IP from NetBox.",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
