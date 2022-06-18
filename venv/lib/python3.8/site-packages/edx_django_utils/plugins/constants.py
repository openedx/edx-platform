"""
Constants/Enums used during interfacing with plugin system
"""

# Name of the class attribute to put in the AppConfig class of the Plugin App.
PLUGIN_APP_CLASS_ATTRIBUTE_NAME = "plugin_app"


# Name of the function that belongs in the plugin Django app's settings file.
# The function should be defined as:
#     def plugin_settings(settings):
#         # enter code that should be injected into the given settings module.
PLUGIN_APP_SETTINGS_FUNC_NAME = "plugin_settings"


class PluginSettings():
    """
    The PluginSettings enum defines dictionary field names (and defaults)
    that can be specified by a Plugin App in order to configure the settings
    that are injected into the project.
    """

    CONFIG = "settings_config"
    RELATIVE_PATH = "relative_path"
    DEFAULT_RELATIVE_PATH = "settings"


class PluginURLs():
    """
    The PluginURLs enum defines dictionary field names (and defaults) that can
    be specified by a Plugin App in order to configure the URLs that are
    injected into the project.
    """

    CONFIG = "url_config"
    APP_NAME = "app_name"
    NAMESPACE = "namespace"
    REGEX = "regex"
    RELATIVE_PATH = "relative_path"
    DEFAULT_RELATIVE_PATH = "urls"


class PluginSignals():
    """
    The PluginSignals enum defines dictionary field names (and defaults)
    that can be specified by a Plugin App in order to configure the signals
    that it receives.
    """

    CONFIG = "signals_config"

    RECEIVERS = "receivers"
    DISPATCH_UID = "dispatch_uid"
    RECEIVER_FUNC_NAME = "receiver_func_name"
    SENDER_PATH = "sender_path"
    SIGNAL_PATH = "signal_path"

    RELATIVE_PATH = "relative_path"
    DEFAULT_RELATIVE_PATH = "signals"


class PluginContexts():
    """
    The PluginContexts enum defines dictionary field names (and defaults)
    that can be specified by a Plugin App in order to configure the
    additional views it would like to add context into.
    """

    CONFIG = "view_context_config"
