from importlib import import_module as system_import_module


def import_module(module_path):
    return system_import_module(module_path)


def get_module_path(app_config, plugin_config, plugin_cls):
    return u'{package_path}.{module_path}'.format(
        package_path=app_config.name,
        module_path=plugin_config.get(plugin_cls.RELATIVE_PATH, plugin_cls.DEFAULT_RELATIVE_PATH),
    )
