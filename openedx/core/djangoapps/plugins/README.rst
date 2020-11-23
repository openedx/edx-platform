Django App Plugins
==================

Provides functionality to enable improved plugin support of Django apps.

Once a Django project is enhanced with this functionality, any participating
Django app (a.k.a. Plugin App) that is PIP-installed on the system is
automatically included in the Django project's INSTALLED_APPS list. In addition,
the participating Django app's URLs and Settings are automatically recognized by
the Django project. Furthermore, the Plugin Signals feature allows Plugin Apps
to shift their dependencies on Django Signal Senders from code-time to runtime.

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


Django Projects
---------------

In order to enable this functionality in a Django project, the project needs to
update:

1. its settings to extend its INSTALLED_APPS to include the Plugin Apps
::

   INSTALLED_APPS.extend(plugin_apps.get_apps(...))

2. its settings to add all Plugin Settings
::

   plugin_settings.add_plugins(__name__, ...)

3. its urls to add all Plugin URLs
::

   urlpatterns.extend(plugin_urls.get_patterns(...))

4. its setup to register PluginsConfig (for connecting Plugin Signals)
::

    from setuptools import setup
    setup(
        ...
        entry_points={
            "lms.djangoapp": [
                "plugins = openedx.core.djangoapps.plugins.apps:PluginsConfig",
            ],
            "cms.djangoapp": [
                "plugins = openedx.core.djangoapps.plugins.apps:PluginsConfig",
            ],
        }
    )


Plugin Apps
-----------

In order to make use of this functionality, plugin apps need to:

1. create an AppConfig class in their apps module, as described in Django's
`Application Configuration <https://docs.djangoproject.com/en/2.0/ref/applications/#django.apps.AppConfig>`_.

2. add their AppConfig class to the appropriate entry point in their setup.py
file::

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

3. configure the Plugin App in their AppConfig
class::

    from django.apps import AppConfig
    from openedx.core.djangoapps.plugins.constants import (
        ProjectType, SettingsType, PluginURLs, PluginSettings, PluginContexts
    )
    class MyAppConfig(AppConfig):
        name = u'full_python_path.my_app'

        # Class attribute that configures and enables this app as a Plugin App.
        plugin_app = {

            # Configuration setting for Plugin URLs for this app.
            PluginURLs.CONFIG: {

                # Configure the Plugin URLs for each project type, as needed.
                ProjectType.LMS: {

                    # The namespace to provide to django's urls.include.
                    PluginURLs.NAMESPACE: u'my_app',

                    # The application namespace to provide to django's urls.include.
                    # Optional; Defaults to None.
                    PluginURLs.APP_NAME: u'my_app',

                    # The regex to provide to django's urls.url.
                    # Optional; Defaults to r''.
                    PluginURLs.REGEX: r'^api/my_app/',

                    # The python path (relative to this app) to the URLs module to be plugged into the project.
                    # Optional; Defaults to u'urls'.
                    PluginURLs.RELATIVE_PATH: u'api.urls',
                }
            },

            # Configuration setting for Plugin Settings for this app.
            PluginSettings.CONFIG: {

                # Configure the Plugin Settings for each Project Type, as needed.
                ProjectType.LMS: {

                    # Configure each Settings Type, as needed.
                    SettingsType.PRODUCTION: {

                        # The python path (relative to this app) to the settings module for the relevant Project Type and Settings Type.
                        # Optional; Defaults to u'settings'.
                        PluginSettings.RELATIVE_PATH: u'settings.production',
                    },
                    SettingsType.COMMON: {
                        PluginSettings.RELATIVE_PATH: u'settings.common',
                    },
                }
            },

            # Configuration setting for Plugin Signals for this app.
            PluginSignals.CONFIG: {

                # Configure the Plugin Signals for each Project Type, as needed.
                ProjectType.LMS: {

                    # The python path (relative to this app) to the Signals module containing this app's Signal receivers.
                    # Optional; Defaults to u'signals'.
                    PluginSignals.RELATIVE_PATH: u'my_signals',

                    # List of all plugin Signal receivers for this app and project type.
                    PluginSignals.RECEIVERS: [{

                        # The name of the app's signal receiver function.
                        PluginSignals.RECEIVER_FUNC_NAME: u'on_signal_x',

                        # The full path to the module where the signal is defined.
                        PluginSignals.SIGNAL_PATH: u'full_path_to_signal_x_module.SignalX',

                        # The value for dispatch_uid to pass to Signal.connect to prevent duplicate signals.
                        # Optional; Defaults to full path to the signal's receiver function.
                        PluginSignals.DISPATCH_UID: u'my_app.my_signals.on_signal_x',

                        # The full path to a sender (if connecting to a specific sender) to be passed to Signal.connect.
                        # Optional; Defaults to None.
                        PluginSignals.SENDER_PATH: u'full_path_to_sender_app.ModelZ',
                    }],
                }
            },

            # Configuration setting for Plugin Contexts for this app.
            PluginContexts.CONFIG: {

                # Configure the Plugin Signals for each Project Type, as needed.
                ProjectType.LMS: {

                    # Key is the view that the app wishes to add context to and the value
                    # is the function within the app that will return additional context
                    # when called with the original context
                    u'course_dashboard': u'my_app.context_api.get_dashboard_context'
                }
            }
        }

OR use string constants when they cannot import from djangoapps.plugins::

    from django.apps import AppConfig
    class MyAppConfig(AppConfig):
        name = u'full_python_path.my_app'

        plugin_app = {
            u'url_config': {
                u'lms.djangoapp': {
                    u'namespace': u'my_app',
                    u'regex': u'^api/my_app/',
                    u'relative_path': u'api.urls',
                }
            },
            u'settings_config': {
                u'lms.djangoapp': {
                    u'production': { relative_path: u'settings.production' },
                    u'common': { relative_path: u'settings.common'},
                }
            },
            u'signals_config': {
                u'lms.djangoapp': {
                    u'relative_path': u'my_signals',
                    u'receivers': [{
                        u'receiver_func_name': u'on_signal_x',
                        u'signal_path': u'full_path_to_signal_x_module.SignalX',
                        u'dispatch_uid': u'my_app.my_signals.on_signal_x',
                        u'sender_path': u'full_path_to_sender_app.ModelZ',
                    }],
                }
            },
            u'view_context_config': {
                u'lms.djangoapp': {
                    'course_dashboard': u'my_app.context_api.get_dashboard_context'
                }
            }
        }

4. For Plugin Settings, insert the following function into each of the Plugin
Settings modules::

    def plugin_settings(settings):
        # Update the provided settings module with any app-specific settings.
        # For example:
        #     settings.FEATURES['ENABLE_MY_APP'] = True
        #     settings.MY_APP_POLICY = 'foo'
