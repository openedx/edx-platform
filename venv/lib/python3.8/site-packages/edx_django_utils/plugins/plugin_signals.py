"""
Allows plugins to work with django signals

Please remember to expose any new public methods in the `__init__.py` file.
"""
from logging import getLogger

from . import constants, registry, utils

log = getLogger(__name__)


def connect_plugin_receivers(project_type):
    """
    connects receivers to right signal
    """
    for signals_module, signals_config in _iter_plugins(project_type):
        for signal, receiver_func, receiver_config in _iter_receivers(
            signals_module, signals_config
        ):
            signal.connect(
                receiver_func,
                sender=_get_sender(receiver_config),
                dispatch_uid=_get_dispatch_uuid(receiver_config, receiver_func),
            )


def _iter_receivers(signals_module, signals_config):
    """
    Generator for ___ TODO
    """
    for receiver_config in signals_config.get(constants.PluginSignals.RECEIVERS, []):
        receiver_func = utils.import_attr_in_module(
            signals_module, receiver_config[constants.PluginSignals.RECEIVER_FUNC_NAME],
        )
        signal = utils.import_attr(receiver_config[constants.PluginSignals.SIGNAL_PATH])
        yield signal, receiver_func, receiver_config


def _iter_plugins(project_type):
    """
    Generator for ___ TODO
    """
    for app_config in registry.get_plugin_app_configs(project_type):
        signals_config = _get_config(app_config, project_type)
        if signals_config is None:
            log.debug(
                "Plugin Apps [Signals]: Did NOT find %s for %s",
                app_config.name,
                project_type,
            )
            continue

        signals_module_path = utils.get_module_path(
            app_config, signals_config, constants.PluginSignals
        )
        signals_module = utils.import_module(signals_module_path)

        log.debug(
            "Plugin Apps [Signals]: Found %s with %d receiver(s) for %s",
            app_config.name,
            len(signals_config.get(constants.PluginSignals.RECEIVERS, [])),
            project_type,
        )
        yield signals_module, signals_config


def _get_config(app_config, project_type):
    plugin_config = getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    signals_config = plugin_config.get(constants.PluginSignals.CONFIG, {})
    return signals_config.get(project_type)


def _get_sender(receiver_config):
    sender_path = receiver_config.get(constants.PluginSignals.SENDER_PATH)
    if sender_path:
        return utils.import_attr(sender_path)
    return None


def _get_dispatch_uuid(receiver_config, receiver_func):
    dispatch_uid = receiver_config.get(constants.PluginSignals.DISPATCH_UID)
    if dispatch_uid is None:
        dispatch_uid = f"{receiver_func.__module__}.{receiver_func.__name__}"
    return dispatch_uid
