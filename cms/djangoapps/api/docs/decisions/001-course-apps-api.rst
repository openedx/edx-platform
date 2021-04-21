Course Apps API
_______________

Status
======
Proposal

Context
=======

The new `Course Authoring MFE`_ includes a new UX called "Pages and Resources"
for configuring course "apps" such as progress, wiki, teams, discussions,
etc. all from one place. Currently, these apps are intermingled with the
core platform and are inseparable from it, however, future apps could be
implemented as plugins.

This ADR proposes a way to configure these apps from the backend that MFEs
can use and potentially enable/disable these apps using an API.

.. _Course Authoring MFE: https://github.com/edx/frontend-app-course-authoring/


Decision
========

We can introduce a new type of Open edX plugin, a course app. These are
course-level apps that add new functionality to the course for students.
Each course app has associated metadata and a standard API to determine if
the app is available, enabled, etc.

This metadata should be made available via a configuration class similar to
that used for Django apps, or course tabs etc. We can develop a new course
apps API that can be driven by the metadata provided by these installed
plugins.

In the context of these apps, we need to distinguish between *installed*,
*available* and *enabled*. The standard plugin API will automatically
discover all installed plugins. However, if a plugin is installed for use
with a subset of courses, there should be a way to only enable it for those
courses. To do this we use have a mechanism to determine availability. Each
app should expose a helper method to check if its availability for a course.

As such the list of *available* apps might not match the list of
*installed* apps since it is possible that certain apps may be disabled,
or otherwise unavailable for a particular course.

The course apps API will  list the available apps, and allow toggling them
on or off. It will not support any other verbs or settings. Each app can
provide its own API(s) for configuring app-specific settings, which will not
be in scope here. Currently the mechanism for extending the frontend with
custom config pages for plug-in apps is TBD.

Each app will have the following associated metadata:

- **id**: (string) A unique identifier for the app.
- **name**: (string) A friendly name for the app that can be shown in the UI.
- **description**: (string) A friendly description of what the app does, to be shown to
  users in the UI.
- **default_enabled**: (boolean) For any new course, does this app default to enabled.
- **enabled**: (boolean) Is this app enabled for the current course.
- **allowed_operations**: (dictionary) Apps can potentially enable/disable certain
  operations. The following operations should be specified for all apps:

    - **enable**: (boolean) Can the current user enable/disable this app.
    - **configure**: (boolean) Can the current user can configure this app.

  If an app doesn't have any configuration it can set the ``configure`` to false
  and the UI will simply not show a configuration option for that app.
- **legacy_link**: (string) If available, this will point to the legacy link for
  configuring the app. This can be provided as a fallback while the new UX is
  still in development.

Here is the structure that will form the basis of the API's response:

.. code-block:: python

    {
        'id': 'courseapp',
        'enabled': False,
        'name': 'Course App',
        'description': 'A sample course app for use as documentation.',
        'allowed_operations': {
            'enable': True,
            'configure': True,
            'edit_lti_config': False,
        },
        'legacy_link': 'https://studio.example.com/course_id/app-page',
    }


This API can be hosted at: ``/course_apps/v1/apps/{course_id}/``

A ``GET`` request to this API will return an array of objects with the above
structure. A ``PATCH`` request to the same endpoint with just the ``id`` and the
`enabled` attribute can be used to enable/disable the app if it's possible to do
so.

Note, as mentioned above, it may not always be possible to enable/disable an
app. Similar to disabling an XBlock from a course that's in use, some apps might
break the course if you remove them while they are in use. In other cases the
app may not support enabling/disabling without changing a setting/django config.
Or an app might need to be configured first before it can be enabled.

This data will be provided by a plugin configuration that is part of the app.
For old/existing apps, we can create plugin configurations that call back to
existing code.

To enumerate the list of available apps, we will list the installed plugins,
check which plugins are available for the current course, and call each plugin
to get its metadata. Each plugin will support checking if it is available for a
particular course. If the plugin marks itself as unavailable, it won't be
listed in the API response.

Only legacy apps will support the ``legacy_link``, it will not be a publicised
part of the API so new/external plugin apps shouldn't use it. This link should
only be provided for course apps that don't have a UI in the course authoring
MFE. If a partial UI exists, the MFE settings view can always link back to the
old studio view from there.

The following is a sample class with the pattern for such plugins:

.. code-block :: python

    class CourseApp:
        app_id: str = 'wiki'
        name: str = 'Wiki'
        description: str = 'A short description of what the Wiki does.'
        # Specify if this app is enabled by default. If the app is made available for a course
        # should it also automatically be considered enabled.
        default_enabled: bool = False

        # This method will not be in the sample/base class, but will be added to
        # existing course apps.
        if LEGACY_APP:
            @classmethod
            def legacy_link(cls, course_key):
                return f'some/link/to/{course_key}'

        @classmethod
        def is_available(cls, course_key):
            # Some mechanism, ideally a waffle flag in the course apps namespace
            # to see if this app can be enabled/configured for this course.
            return True

        @classmethod
        def is_enabled(cls, course_key):
            # Some logic to check if the app is enabled for this course
            # This will not vary from user-to-user in studio.
            return True

        @classmethod
        def set_enabled(cls, course_key, user, enabled):
            # Some logic to enable the app for this course.
            # The user here isn't passed on for permission checking, but just
            # for logging/auditing.
            return enabled

        @classmethod
        def get_allowed_operations(cls, course_key, user):
            # This should return a dictionary with at least the `enable` and `configure` keys.
            return {
                'enable': can_user_enable(course_key, user),
                'configure': can_user_configure(course_key, user),
            }


For each existing course app, we can create such a class and have these class
methods call back to the existing code for the same.

Consequences
============

- A new course apps API that consistently uses a standard mechanism (a plugin
  class) for discovering course apps, determining their availability and
  enabling/disabling them.
- We still leave the more complex considerations of configuration to each
  individual app to implement in its own best way. i.e. the aim here isn't to
  have a uniform API to configure all course apps.
