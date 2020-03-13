Plugin Contexts
---------------

Status
======
Draft

Context
=======
edx-platform contains a plugin system which allows new Django apps to be installed inside the LMS and Studio without requiring the LMS/Studio to know about them. This is what enables us to move to a small and extensible core. While we had the ability to add settings, URLs, and signal handlers in our plugins, we wasn't a any way for a plugin to affect the commonly used pages that the core was delivering. Thus a plugin couldn't change any details on the dashboard, courseware, or any other rendered page that the platform delivered.

Decisions
=========
We have added the ability to add page context additions to the plugin system. This means that a plugin will be able to add context any view where it is enabled. To support this we have decided:
# Plugins will define a callable function that the LMS and/or studio can import and call, which will return additional context to be added.
# Every page that a plugin wants to add context to, must add a line to add the plugin contexts directly before the render.
# All view + plugin data will exist in the same dictionary. To better protect against dictionary key collisions, it is suggested that you prefix your new context items with your app name (e.g. return {"myapp__some_variable": True} vs {"some_variable": True})
# Each view will have a constant name that will be defined within it's app's API.py which will be used by plugins. These must be globally unique. These will also be recorded in the rendering app's README.rst file.
# Plugin app's may import the view name from the rendering app's api.py or just use it's string.
# For now, in order to use these new context data items, we must use theming alongside this to keep the new context out of the core. This may be iterated on in the future.

Implementation
--------------

In the plugin app
~~~~~~~~~~~~~~~~~
Config
++++++
Inside of your AppConfig your new plugin app, add a "context_config" item like below.
* The format will be {"globally_unique_view_name": "function_inside_plugin_app"}
* The function name & path don't need to be named anything specific, so long as they work
* These functions will be called on **every** render of that view, so keep them efficient or memoize them if they aren't user specific.

::
    class MyAppConfig(AppConfig):
        name = "my_app"

        plugin_app = {
            "context_config": {
                "lms.djangoapp":  {
                    "course_dashboard": "my_app.context_api.get_dashboard_context"
                }
            }
        }

Function
++++++++
The function that will be called by the plugin system should accept a single parameter which will be the previously existing context. It should then return a dictionary which consists of items which will be added to the context

Example:
::
    def my_context_function(existing_context):
        additional_context = {"myapp__some_variable": 10}
        if existing_context.get("some_value"):
            additional_context.append({"myapp__some_other_variable": True})
        return additional_context


In the core (LMS / Studio)
~~~~~~~~~~~~~~~~~~~~~~~~~~
The view you wish to add context to should have the following pieces enabled:

* A constant defined inside the app's for the globally unique view name.
* The view must call lines similar to the below right before the render so that the plugin has the full context.
::
    context_from_plugins = get_plugins_view_context(
        plugin_constants.ProjectType.LMS,
        current_app.api.THIS_VIEW_NAME,
        context
    )
    context.update(context_from_plugins)

