Plugin Slots
------------

Status
======
Draft

Context
=======
edx-platform contains a plugin system (https://github.com/edx/edx-platform/tree/master/openedx/core/djangoapps/plugins)
which allows new Django apps to be installed inside the LMS and Studio without
requiring the LMS/Studio to know about them. This is what enables us to move to
a small and extensible core. While it's possible to extend the content of pages
rendered by the platform using templates, via certain extension points that allow
injecting content into 'head-extra', 'body-initial' etc slots in the base template,
it isn't possible for plugins to inject content at all.

Decisions
=========
We have added the ability for plugins to render content into existing pages. To
support this, we have decided:

* A template can how declare slots into which a plugin can inject content, by
  using the `plugin_slot` template tag (for Django template) or function (for
  Mako templates).
* Plugins can define a callable function that the LMS or Studio can import and
  call. This function will be called with minimal context, and in turn supports
  pluggable contexts.
* The callable function should return direct HTML content as text that can be
  rendered on page.
* Each view can provide an list of what context data should be made available to
  all plugins by adding it to the context itself in a list called
  `context_allow_list`. This will need to be maintained across releases so
  should be kept to a bare minimum.
* A plugin will need to specify the namespace in which that slot should be active.
  Different views can be under different namespaces, such as:
  - 'course_home'
  - 'learner_dashboard'
  - 'instructor_dashboard'
* All templates/pages will support three slots:
   + ``head-extra``: This slot exists near the end of the header tag for each page
     and can be used to add scripts, metadata, stylesheets or other header content.
     It is equivalent to adding a 'head-extra.html' template file.
   + ``body-initial``: This slot exists at the start of the page, right after the
     opening of the body tag. It is equivalent to adding a 'body-initial.html'
     template file.
   + ``body-extra``: This slot exists at the end of the page near the closing of
     the body tag. It is equivalent to adding a 'body-extra.html' template file.

Implementation
==============

In the plugin app
~~~~~~~~~~~~~~~~~

Config
++++++

Inside of the AppConfig of your new plugin app, add a "slots_config" item like below.

* The format will be ``{"slot_name": "function_inside_plugin_app"}``
* The function name & path don't need to be named anything specific, so long as they work
* These functions will be called on **every** render of that view, so keep them
  efficient or memoize them if they aren't user specific.

.. code-block:: python

    class MyAppConfig(AppConfig):
        name = "my_app"

        plugin_app = {
            "slots_config": {
                "lms.djangoapp":  {
                    "view_namespace": {
                        "body-initial": "my_app.slots_api.get_body_initial_content"
                    }
                }
            }
        }

Function
++++++++
The function that will be called by the plugin system should accept a single
parameter which will be the context for that slot. It should then return an
HTML string that will be injected in the specified slot.

Example:

.. code-block:: python

    def my_slot_function(context):
        return render_to_string('my_app/template.html', context=context)


In the core (LMS / Studio)
~~~~~~~~~~~~~~~~~~~~~~~~~~
The view you wish to add slots to should have the following pieces enabled:

* A constant defined inside the apps for the slot name.
* Decorate the view with `@view_namespace("namespace")` to make it work with
  slots in that namespace. (This  should be the very first decorator on that
  view function).
* The view can add an entry called `context_allow_list` to its context. This
  should either be equal to '*', or be a list of context entries that are
  allowed to be passed to plugin slots. If omitted, only the current request
  and url are passed through.
* The template can include a line like the following to declare a new slot.

  ``${plugin_slot(context, 'lms.djangoapp', 'slot_name') | n}``

  Here ``lms.djangoapp`` or ``studio.djangoapp`` can be used to specify if this
  is an slot in the LMS or Studio. The slot name should be unique for each
  project.
