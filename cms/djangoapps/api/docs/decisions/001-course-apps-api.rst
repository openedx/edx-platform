Course Apps API
_______________

Status
======
Proposal

Context
=======

The new `Course Authoring MFE`_ includes a new UX called "Pages and Resources"
for configuring course "apps" such as progress, wiki, teams, discussions etc.
all from one place. Currently these apps are intermingled with the core
platform and are inseparable from it, however future apps could be implemented
as plugins.

In order to drive this new UI, we need a way to discover installed and available
course apps and provide an API that can be used by MFEs to display information
related to these apps and potentially enable/disable these apps.

.. _Course Authoring MFE: https://github.com/edx/frontend-app-course-authoring/


Decision
========

We can develop a new course apps API that can be used to manage the apps
available for a course. The list of *available* apps might not match the list
of *installed* apps since it is possible that certain apps may be disabled, or
otherwise unavailable for a particular course.

The course apps API will only list the available apps, and allow toggling them
on or off. It will not support any other verbs or settings. Each app can
provide its own API(s) for configuring app-specific settings, which will not be
in scope here. Currently the mechanism for extending the frontend with custom
config pages for plug-in apps is TBD.

Each app will have the following associated metadata:

- **id**: A unique identifier for the app. This can be used in the frontend to
  look up the app's friendly title and description.
- **enabled**: Is this app enabled for the current course.
- **permissions**: Apps can potentially enable/disable certain operations, for
  users based on their role. The permissions a user has can be listed here. Apps
  may have their own permissions but at this very least this will include:

    - **enable**: Can the current user enable/disable this app.
    - **configure**: Can the current user can configure this app.

  Apps may have their own custom fine-grained controls over what settings a
  particular user can configure.

  If an app doesn't have any configuration it can leave out the ``configure``
  key and the UI will simply not show a configuration option for that app.
- **legacy_link**: If available, this will point to the legacy link for
  configuring the app. This can be provided as a fallback while the new UX is
  still in development.

Here is the structure that will form the basis of the API's response:

.. code-block:: python

    {
        'id': 'courseapp',
        'enabled': False,
        'permissions': {
            'enable': True,
            'configure': True,
            'edit_lti_config': False,
        },
        'legacy_link': 'https://studio.example.com/course_id/app-page',
    }


This API can be hosted at: ``/course_apps/v1/apps/{course_id}/``

A ``GET`` request to this API will return an array of objects with the above
structure. A ``PATCH`` request to the same endpoint with just the ``id`` and the
`enabled` attribute can be used to enable/disable the app if the user has the
requisite permissions.

Each app will also have a user-friendly title and description, however this will
be defined in the frontend since that is where internationalisation will happen.
The frontend can look up the title and description based on the app's ``id``.

This data will be provided by a plugin configuration that is part of the app.
For old/existing apps, we can create plugin configurations that call back to
existing code.

To maintain consistency around how a course app is enabled/disabled, we can use
Course Waffle Flags as the mechanism for enabling/disabling a course app for a
particular course or globally. We can create a new Waffle namespace called
"course_apps", and the course app ID can be the name for the
``CourseWaffleFlag`` for each plugin by convention.

To enumerate the list of available apps, we will list the installed plugins,
check which plugins are available for the current course, and call each plugin
to get its metadata. Each plugin will support checking if the plugin is
available for a particular course. If the plugin marks itself as unavailable, it
won't be listed in the API response.

Only legacy apps will support the ``legacy_link``, it will not be a publicised
part of the API so new/external plugin apps shouldn't use it. This link should
only be provided for course apps that don't have a UI in the course authoring
MFE. If a partial UI exists, the MFE settings view can always link back to the
old studio view from there.

The following is a sample class with the pattern for such plugins:

.. code-block :: python

    WIKI_ENABLED = CourseWaffleFlag(COURSE_APPS_WAFFLE_NAMESPACE, 'wiki', __name__)

    class CourseApp:
        app_id: str = 'wiki'

        IS_AVAILABLE = WIKI_ENABLED

        # This method will not be in the sample/base class, but will be added to
        # existing course apps.
        if LEGACY_APP:
            @classmethod
            def legacy_link(cls, course_key):
                return f'some/link/to/{course_key}'

        @classmethod
        def is_enabled(cls, course_key):
            # Some logic to check if the app is enabled for this course
            # This will not vary from user-to-user in studio.
            return True

        @classmethod
        def get_permissions(cls, course_key, user):
            # This should return a dictionary with at least an `enable` key.
            return {
                'enable': can_user_enable(course_key, user),
                'configure': can_user_configure(course_key, user),
                'edit_lti_config': is_user_admin(course_key, user),
            }


For each existing course app, we can create such a class and have these class
methods call back to the existing code for the same.

Consequences
============

- A new course apps API that consistently uses only a single mechanism for
  discovering course apps, determining their availability and enabling/disabling
  them.
- We still leave the more complex considerations of configuration to each
  individual app to implement in its own best way. i.e. the AIM here isn't to
  have a uniform API to configure all course apps.
