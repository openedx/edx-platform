Plugin Contexts
---------------

Status
======
Draft

Context
=======
edx-platform contains a plugin system (https://github.com/edx/edx-platform/tree/master/openedx/core/djangoapps/plugins) which allows new Django apps to be installed inside the LMS and Studio without requiring the LMS/Studio to know about them. This is what enables us to move to a small and extensible core. While we had the ability to add settings, URLs, and signal handlers in our plugins, there wasn't any way for a plugin to affect the commonly used pages that the core was delivering. Thus a plugin couldn't change any details on the dashboard, courseware, or any other rendered page that the platform delivered.

Decisions
=========
We have added the ability to add page context additions to the plugin system. This means that a plugin will be able to add context to any view where it is enabled. To support this we have decided:

1. Plugins will define a callable function that the LMS and/or studio can import and call, which will return additional context to be added.
2. Every page that a plugin wants to add context to, must add a line to add the plugin contexts directly before the render.
3. Plugin context will live in a dictionary called "plugins" that will be passed into the context the templates receive. The structure will look like:

    .. code-block::

        {
            ..existing context values..
            "plugins": {
                "my_new_plugin": {... my_new_plugins's values ...},
                "my_other_plugin": {... my_other_plugin's values ...},
            }
        }

4. Each view will have a constant name that will be defined within it's app's API.py which will be used by plugins. These must be globally unique. These will also be recorded in the rendering app's README.rst file.
5. Plugin apps have the option to either use the view name strings directly or import the constants from the rendering app's api.py if the plugin is part of the edx-platform repo.
6. For now, in order to use these new context data items, we must use theming alongside this to keep the new context out of the core. This may be iterated on in the future.

Implementation
==============

In the plugin app
~~~~~~~~~~~~~~~~~
Config
++++++
Inside of the AppConfig of your new plugin app, add a "view_context_config" item like below.

* The format will be ``{"globally_unique_view_name": "function_inside_plugin_app"}``
* The function name & path don't need to be named anything specific, so long as they work
* These functions will be called on **every** render of that view, so keep them efficient or memoize them if they aren't user specific.

    .. code-block::

        class MyAppConfig(AppConfig):
        name = "my_app"

        plugin_app = {
            "view_context_config": {
                "lms.djangoapp":  {
                    "course_dashboard": "my_app.context_api.get_dashboard_context"
                }
            }
        }

Function
++++++++
The function that will be called by the plugin system should accept a single parameter which will be the previously existing context. It should then return a dictionary which consists of items which will be added to the context

Example:
    .. code-block::

        def my_context_function(existing_context, *args, **kwargs):
            additional_context = {"some_plugin_value": 10}
            if existing_context.get("some_core_value"):
                additional_context.append({"some_other_plugin_value": True})
            return additional_context


In the core (LMS / Studio)
~~~~~~~~~~~~~~~~~~~~~~~~~~
The view you wish to add context to should have the following pieces enabled:

* A constant defined inside the app's for the globally unique view name.
* The view must call lines similar to the below right before the render so that the plugin has the full context.
    .. code-block::

        context_from_plugins = get_plugins_view_context(
            plugin_constants.ProjectType.LMS,
            current_app.api.THIS_VIEW_NAME,
            context
        )
        context.update(context_from_plugins)

