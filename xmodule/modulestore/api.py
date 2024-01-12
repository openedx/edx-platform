"""
Python APIs for the xmodule.modulestore module.
"""

from django.conf import settings


def get_root_module_name(class_or_function):
    """
    Return the root module name for the given class or function.
    """
    module_path = class_or_function.__module__
    return module_path.split('.')[0]


def get_xblock_root_module_name(block):
    """
    Return the XBlock Python module name.
    """
    # `xblock.unmixed_class` is a property added by the XBlock library to add mixins to the class which conceals
    # the original class properties.
    xblock_original_class = getattr(block, 'unmixed_class', block.__class__)
    return get_root_module_name(xblock_original_class)


def get_python_locale_root():
    """
    Return the XBlock locale root directory for OEP-58 translations.
    """
    return settings.REPO_ROOT / 'conf/plugins-locale/xblock.v1'


def get_javascript_i18n_file_name(xblock_module, locale):
    """
    Return the relative path to the JavaScript i18n file.

    Relative to the /static/ directory.
    """
    return f'js/xblock.v1-i18n/{xblock_module}/{locale}.js'


def get_javascript_i18n_file_path(xblock_module, locale):
    """
    Return the absolute path to the JavaScript i18n file.
    """
    return settings.STATICI18N_ROOT / get_javascript_i18n_file_name(xblock_module, locale)
