
"""
Common settings for Admin Dashboard
"""


def plugin_settings(settings):
    settings.MAKO_TEMPLATE_DIRS_BASE.append(
      settings.OPENEDX_ROOT / 'features' / 'wikimedia_features' / 'admin_dashboard' / 'templates',
    )
