"""
Plugins infrastructure

See README.rst for details.
"""

from .constants import PluginContexts, PluginSettings, PluginSignals, PluginURLs
from .pluggable_override import pluggable_override
from .plugin_apps import get_plugin_apps
from .plugin_contexts import get_plugins_view_context
from .plugin_manager import PluginError, PluginManager
from .plugin_settings import add_plugins
from .plugin_signals import connect_plugin_receivers
from .plugin_urls import get_plugin_url_patterns
from .registry import get_plugin_app_configs
