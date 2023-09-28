"""Devstack environment variables unique to the instructor plugin."""


def plugin_settings(settings):
    """Settings for the instructor plugin."""
    # Set this to the dashboard URL in order to display the link from the
    # dashboard to the Analytics Dashboard.
    settings.ANALYTICS_DASHBOARD_URL = None
