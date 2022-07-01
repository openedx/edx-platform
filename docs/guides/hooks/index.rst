Openedx Hooks Extension Framework
=================================

To sustain the growth of the Open edX ecosystem, the business rules of the
platform must be open for extension following the open-closed principle. This
framework allows developers to do just that without needing to fork and modify
the main edx-platform repository.


Context
-------

Hooks are predefined places in the edx-platform core where externally defined
functions can take place. In some cases, those functions can alter what the user
sees or experiences in the platform. Other cases are informative only. All cases
are meant to be extended using Open edX plugins and configuration.

Hooks can be of two types, events and filters. Events are in essence signals, in
that they are sent in specific application places and whose listeners can extend
functionality. On the other hand Filters are passed data and can act on it
before this data is put back in the original application flow. In order to allow
extension developers to use the Events and Filters definitions on their plugins,
both kinds of hooks are defined in lightweight external libraries.

* `openedx filters`_
* `openedx events`_

Hooks are designed with stability in mind. The main goal is that developers can
use them to change the functionality of the platform as needed and still be able
to migrate to newer open releases with very little to no development effort. In
the case of the events, this is detailed in the `versioning ADR`_ and the
`payload ADR`_.

A longer description of the framework and it's history can be found in `OEP 50`_.

.. _OEP 50: https://open-edx-proposals.readthedocs.io/en/latest/oep-0050-hooks-extension-framework.html
.. _versioning ADR: https://github.com/eduNEXT/openedx-events/blob/main/docs/decisions/0002-events-naming-and-versioning.rst
.. _payload ADR: https://github.com/eduNEXT/openedx-events/blob/main/docs/decisions/0003-events-payload.rst
.. _openedx filters: https://github.com/eduNEXT/openedx-filters
.. _openedx events: https://github.com/eduNEXT/openedx-events

On the technical side events are implemented through django signals which makes
them run in the same python process as the lms or cms. Furthermore, events block
the running process. Listeners of an event are encouraged to monitor the
performance or use alternative arch patterns such as receiving the event and
defer to launching async tasks than do the slow processing.


How to use
----------

Using openedx-events in your code is very straight forward. We can consider the
two possible cases, sending or receiving an event.


Receiving events
^^^^^^^^^^^^^^^^

This is one of the most common use cases for plugins. The edx-platform will send
and event and you want to react to it in your plugin.

For this you need to:

1. Include openedx-events in your dependencies.
2. Connect your receiver functions to the signals being sent.

Connecting signals can be done using regular django syntax:

.. code-block:: python

    from openedx_events.learning.signals import SESSION_LOGIN_COMPLETED

    @receiver(SESSION_LOGIN_COMPLETED)
    # your receiver function here


Or at the apps.py

.. code-block:: python

    "signals_config": {
        "lms.djangoapp": {
            "relative_path": "your_module_name",
            "receivers": [
                {
                    "receiver_func_name": "your_receiver_function",
                    "signal_path": "openedx_events.learning.signals.SESSION_LOGIN_COMPLETED",
                },
            ],
        }
    },

In case you are listening to an event in the edx-platform repo, you can directly
use the django syntax since the apps.py method will not be available without the
plugin.


Sending events
^^^^^^^^^^^^^^

Sending events requires you to import both the event definition as well as the
attr data classes that encapsulate the event data.

.. code-block:: python

    from openedx_events.learning.data import UserData, UserPersonalData
    from openedx_events.learning.signals import STUDENT_REGISTRATION_COMPLETED

    STUDENT_REGISTRATION_COMPLETED.send_event(
        user=UserData(
            pii=UserPersonalData(
                username=user.username,
                email=user.email,
                name=user.profile.name,
            ),
            id=user.id,
            is_active=user.is_active,
        ),
    )

You can do this both from the edx-platform code as well as from an openedx
plugin.


Testing events
^^^^^^^^^^^^^^

Testing your code in CI, specially for plugins is now possible without having to
import the complete edx-platform as a dependency.

To test your functions you need to include the openedx-events library in your
testing dependencies and make the signal connection in your test case.

.. code-block:: python

    from openedx_events.learning.signals import STUDENT_REGISTRATION_COMPLETED

    def test_your_receiver(self):
        STUDENT_REGISTRATION_COMPLETED.connect(your_function)
        STUDENT_REGISTRATION_COMPLETED.send_event(
            user=UserData(
                pii=UserPersonalData(
                    username='test_username',
                    email='test_email@example.com',
                    name='test_name',
                ),
                id=1,
                is_active=True,
            ),
        )

        # run your assertions


Changes in the openedx-events library that are not compatible with your code
should break this kind of test in CI and let you know you need to upgrade your
code.


Live example
^^^^^^^^^^^^

For a complete and detailed example you can see the `openedx-events-2-zapier`_
plugin. This is a fully functional plugin that connects to
``STUDENT_REGISTRATION_COMPLETED`` and ``COURSE_ENROLLMENT_CREATED`` and sends
the relevant information to zapier.com using a webhook.

.. _openedx-events-2-zapier: https://github.com/eduNEXT/openedx-events-2-zapier


Index of Events
-----------------

This list contains the events currently being sent by edx-platform. The provided
links target both the definition of the event in the openedx-events library as
well as the trigger location in this same repository.


.. list-table::
   :widths: 35 50 20

   * - *Name*
     - *Type*
     - *Date added*

   * - `STUDENT_REGISTRATION_COMPLETED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L18>`_
     - org.openedx.learning.student.registration.completed.v1
     - `2021-09-02 <https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/register.py#L258>`__

   * - `SESSION_LOGIN_COMPLETED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L30>`_
     - org.openedx.learning.auth.session.login.completed.v1
     - `2021-09-02 <https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/login.py#L306>`__

   * - `COURSE_ENROLLMENT_CREATED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L42>`_
     - org.openedx.learning.course.enrollment.created.v1
     - `2021-09-02 <https://github.com/edx/edx-platform/blob/master/common/djangoapps/student/models.py#L1675>`__

   * - `COURSE_ENROLLMENT_CHANGED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L54>`_
     - org.openedx.learning.course.enrollment.changed.v1
     - `2021-09-22 <https://github.com/edx/edx-platform/blob/master/common/djangoapps/student/models.py#L1675>`__

   * - `COURSE_UNENROLLMENT_COMPLETED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L66>`_
     - org.openedx.learning.course.unenrollment.completed.v1
     - `2021-09-22 <https://github.com/edx/edx-platform/blob/master/common/djangoapps/student/models.py#L1468>`__

   * - `CERTIFICATE_CREATED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L78>`_
     - org.openedx.learning.certificate.created.v1
     - `2021-09-22 <https://github.com/edx/edx-platform/blob/master/lms/djangoapps/certificates/models.py#L506>`__

   * - `CERTIFICATE_CHANGED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L90>`_
     - org.openedx.learning.certificate.changed.v1
     - `2021-09-22 <https://github.com/edx/edx-platform/blob/master/lms/djangoapps/certificates/models.py#L475>`__

   * - `CERTIFICATE_REVOKED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L102>`_
     - org.openedx.learning.certificate.revoked.v1
     - `2021-09-22 <https://github.com/edx/edx-platform/blob/master/lms/djangoapps/certificates/models.py#L397>`__

   * - `COHORT_MEMBERSHIP_CHANGED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L114>`_
     - org.openedx.learning.cohort_membership.changed.v1
     - `2021-09-22 <https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/course_groups/models.py#L135>`__
