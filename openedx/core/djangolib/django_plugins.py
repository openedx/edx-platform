"""
Provides functionality to enable improved plugin support of Django apps.

Once a Django project is enhanced with this functionality, any participating
Django app (a.k.a. Plugin App) that is PIP-installed on the system is
automatically included in the Django project's INSTALLED_APPS list. In addition,
the participating Django app's URLs and Settings are automatically recognized by
the Django project.

While Django+Python already support dynamic installation of components/apps,
they do not have out-of-the-box support for plugin apps that auto-install
into a containing Django project.

This Django App Plugin functionality allows for Django-framework code to be
encapsulated within each Django app, rather than having a monolith Project that
is aware of the details of its Django apps. It is motivated by the following
design principles:

* Single Responsibility Principle, which says "a class or module should have
one, and only one, reason to change." When code related to a single Django app
changes, there's no reason for its containing project to also change. The
encapsulation and modularity resulting from code being co-located with its
owning Django app helps prevent "God objects" that have too much responsibility
and knowledge of the details.

* Open Closed Principle, which says "software entities should be open for
extension, but closed for modification." The edx-platform is extensible via
installation of Django apps. Having automatic Django App Plugin support allows
for this extensibility without modification to the edx-platform. Going forward,
we expect this capability to be widely used by external repos that depend on and
enhance the edx-platform without the need to modify the core platform.

* Dependency Inversion Principle, which says "high level modules should not
depend upon low level modules." The high-level module here is the Django
project, while the participating Django app is the low-level module. For
long-term maintenance of a system, dependencies should go from low-level
modules/details to higher level ones.


== Django Projects ==
In order to enable this functionality in a Django project, the project needs to
update:

1. its settings to extend its INSTALLED_APPS to include the Plugin Apps:
    INSTALLED_APPS.extend(DjangoAppRegistry.get_plugin_apps(...))

2. its settings to add all Plugin Settings:
    DjangoAppRegistry.add_plugin_settings(__name__, ...)

3. its urls to add all Plugin URLs:
    urlpatterns.extend(DjangoAppRegistry.get_plugin_url_patterns(...))


== Plugin Apps ==
In order to make use of this functionality, plugin apps need to:

1. create an AppConfig class in their apps module, as described in
https://docs.djangoproject.com/en/2.0/ref/applications/#django.apps.AppConfig.

2. add their AppConfig class to the appropriate entry point in their setup.py
file:

    from setuptools import setup
    setup(
        ...
        entry_points={
            "lms.djangoapp": [
                "my_app = full_python_path.my_app.apps:MyAppConfig",
            ],
            "cms.djangoapp": [
            ],
        }
    )

3. configure the Plugin App in their AppConfig class:

    from django.apps import AppConfig
    from openedx.core.djangolib.django_plugins import (
        ProjectType, SettingsType, PluginURLs, PluginSettings
    )
    class MyAppConfig(AppConfig):
        name = u'full_python_path.my_app'

        # Class attribute that configures and enables this app as a Plugin App.
        plugin_app = {

            # Configuration setting for Plugin URLs for this app.
            PluginURLs.CONFIG: {

                # Configure the Plugin URLs for each project type, as needed.
                ProjectType.LMS: {

                    # The namespace to provide to django's urls.include, per
                    # https://docs.djangoproject.com/en/2.0/topics/http/urls/#url-namespaces
                    PluginURLs.NAMESPACE: u'my_app',

                    # The regex to provide to django's urls.url.
                    PluginURLs.REGEX: u'api/my_app/',

                    # The python path (relative to this app) to the URLs module
                    # to be plugged into the project.
                    PluginURLs.RELATIVE_PATH: u'api.urls',
                }
            },


            # Configuration setting for Plugin Settings for this app.
            PluginSettings.CONFIG: {

                # Configure the Plugin Settings for each Project Type, as
                # needed.
                ProjectType.LMS: {

                    # Configure each Settings Type, as needed.
                    SettingsType.AWS: {
                        # The python path (relative to this app) to the settings
                        # module for the relevant Project Type and Settings
                        # Type.
                        PluginSettings.RELATIVE_PATH: u'settings.aws',
                    },
                    SettingsType.COMMON: {
                        PluginSettings.RELATIVE_PATH: u'settings.common',
                    },
                }
            }
        }

OR use string constants when you cannot import from django_plugins.

    from django.apps import AppConfig
    class MyAppConfig(AppConfig):
        name = u'full_python_path.my_app'

        plugin_app = {
            u'url_config': {
                u'lms.djangoapp': {
                    u'namespace': u'my_app',
                    u'regex': u'api/my_app/',
                    u'relative_path': u'api.urls',
                }
            },
            u'settings_config': {
                u'lms.djangoapp': {
                    u'aws': { relative_path: u'settings.aws' },
                    u'common': { relative_path: u'settings.common'},
                }
            }
        }

4. For Plugin Settings, insert the following function into each of the plugin
settings modules:
    def plugin_settings(settings):
        # Update the provided settings module with any app-specific settings.
        # For example:
        #     settings.FEATURES['ENABLE_MY_APP'] = True
        #     settings.MY_APP_POLICY = 'foo'

"""
from importlib import import_module
from django.conf.urls import include, url
from logging import getLogger
from openedx.core.lib.plugins import PluginManager


log = getLogger(__name__)


# Name of the class attribute to put in the AppConfig class of the Plugin App.
PLUGIN_APP_CLASS_ATTRIBUTE_NAME = u'plugin_app'


# Name of the function that belongs in the plugin Django app's settings file.
# The function should be defined as:
#     def plugin_settings(settings):
#         # enter code that should be injected into the given settings module.
PLUGIN_APP_SETTINGS_FUNC_NAME = u'plugin_settings'


class ProjectType(object):
    """
    The ProjectType enum defines the possible values for the Django Projects
    that are available in the edx-platform. Plugin apps use these values to
    declare explicitly which projects they are extending.
    """
    LMS = u'lms.djangoapp'
    CMS = u'cms.djangoapp'


class SettingsType(object):
    """
    The SettingsType enum defines the possible values for the settings files
    that are available for extension in the edx-platform. Plugin apps use these
    values (in addition to ProjectType) to declare explicitly which settings
    (in the specified project) they are extending.

    See https://github.com/edx/edx-platform/master/lms/envs/docs/README.rst for
    further information on each Settings Type.
    """
    AWS = u'aws'
    COMMON = u'common'
    DEVSTACK = u'devstack'
    TEST = u'test'


class PluginSettings(object):
    """
    The PluginSettings enum defines dictionary field names (and defaults)
    that can be specified by a Plugin App in order to configure the settings
    that are injected into the project.
    """
    CONFIG = u'settings_config'
    RELATIVE_PATH = u'relative_path'
    DEFAULT_RELATIVE_PATH = u'settings'


class PluginURLs(object):
    """
    The PluginURLs enum defines dictionary field names (and defaults) that can
    be specified by a Plugin App in order to configure the URLs that are
    injected into the project.
    """
    CONFIG = u'url_config'
    APP_NAME = u'app_name'
    NAMESPACE = u'namespace'
    REGEX = u'regex'
    RELATIVE_PATH = u'relative_path'
    DEFAULT_RELATIVE_PATH = u'urls'


class DjangoAppRegistry(PluginManager):
    """
    The DjangoAppRegistry class encapsulates the functionality to enable
    improved plugin support of Django apps.
    """

    @classmethod
    def get_plugin_apps(cls, project_type):
        """
        Returns a list of all registered Plugin Apps, expected to be added to
        the INSTALLED_APPS list for the given project_type.
        """
        plugin_apps = [
            u'{module_name}.{class_name}'.format(
                module_name=app_config.__module__,
                class_name=app_config.__name__,
            )
            for app_config in cls._get_app_configs(project_type)
            if getattr(app_config, PLUGIN_APP_CLASS_ATTRIBUTE_NAME, None) is not None
        ]
        log.info(u'Plugin Apps: Found %s', plugin_apps)
        return plugin_apps

    @classmethod
    def add_plugin_settings(cls, settings_path, project_type, settings_type):
        """
        Updates the module at the given ``settings_path`` with all Plugin
        Settings appropriate for the given project_type and settings_type.
        """
        settings_module = import_module(settings_path)
        for plugin_settings in cls._iter_plugin_settings(project_type, settings_type):
            settings_func = getattr(plugin_settings, PLUGIN_APP_SETTINGS_FUNC_NAME)
            settings_func(settings_module)

    @classmethod
    def get_plugin_url_patterns(cls, project_type):
        """
        Returns a list of all registered Plugin URLs, expected to be added to
        the URL patterns for the given project_type.
        """
        return [
            url(
                url_config.get(PluginURLs.REGEX, r''),
                include(
                    url_module_path,
                    app_name=url_config.get(PluginURLs.APP_NAME),
                    namespace=url_config[PluginURLs.NAMESPACE],
                ),
            )
            for url_module_path, url_config in cls._iter_installable_urls(project_type)
        ]

    @classmethod
    def _iter_plugin_settings(cls, project_type, settings_type):
        """
        Yields Plugin Settings modules that are registered for the given
        project_type and settings_type.
        """
        for app_config in cls._get_app_configs(project_type):
            settings_config = _get_settings_config(app_config, project_type, settings_type)
            if settings_config is None:
                log.info(
                    u'Plugin Apps [Settings]: Did NOT find %s for %s and %s',
                    app_config.name,
                    project_type,
                    settings_type,
                )
                continue

            plugin_settings_path = _get_module_path(app_config, settings_config, PluginSettings)
            log.info(u'Plugin Apps [Settings]: Found %s for %s and %s', app_config.name, project_type, settings_type)
            yield import_module(plugin_settings_path)

    @classmethod
    def _iter_installable_urls(cls, project_type):
        """
        Yields the module path and configuration for Plugin URLs registered for
        the given project_type.
        """
        for app_config in cls._get_app_configs(project_type):
            url_config = _get_url_config(app_config, project_type)
            if url_config is None:
                log.info(u'Plugin Apps [URLs]: Did NOT find %s for %s', app_config.name, project_type)
                continue

            urls_module_path = _get_module_path(app_config, url_config, PluginURLs)
            url_config[PluginURLs.NAMESPACE] = url_config.get(PluginURLs.NAMESPACE, app_config.name)
            log.info(
                u'Plugin Apps [URLs]: Found %s with namespace %s for %s',
                app_config.name,
                url_config[PluginURLs.NAMESPACE],
                project_type,
            )
            yield urls_module_path, url_config

    @classmethod
    def _get_app_configs(cls, project_type):
        return cls.get_available_plugins(project_type).itervalues()


def _get_module_path(app_config, plugin_config, plugin_cls):
    return u'{package_path}.{module_path}'.format(
        package_path=app_config.name,
        module_path=plugin_config.get(plugin_cls.RELATIVE_PATH, plugin_cls.DEFAULT_RELATIVE_PATH),
    )


def _get_settings_config(app_config, project_type, settings_type):
    plugin_config = getattr(app_config, PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    settings_config = plugin_config.get(PluginSettings.CONFIG, {})
    project_type_settings = settings_config.get(project_type, {})
    return project_type_settings.get(settings_type)


def _get_url_config(app_config, project_type):
    plugin_config = getattr(app_config, PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    url_config = plugin_config.get(PluginURLs.CONFIG, {})
    return url_config.get(project_type)
