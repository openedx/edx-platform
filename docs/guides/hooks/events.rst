Open edX Events
===============

How to use
----------

Using openedx-events in your code is very straight forward. We can consider the
two possible cases, sending or receiving an event.


Receiving events
^^^^^^^^^^^^^^^^

This is one of the most common use cases for plugins. The edx-platform will send
an event and you want to react to it in your plugin.

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


Learning Events
^^^^^^^^^^^^^^^

.. list-table::
   :widths: 35 50 20

   * - *Name*
     - *Type*
     - *Date added*

   * - `STUDENT_REGISTRATION_COMPLETED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L24>`_
     - org.openedx.learning.student.registration.completed.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/register.py#L262>`_

   * - `SESSION_LOGIN_COMPLETED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L36>`_
     - org.openedx.learning.auth.session.login.completed.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/login.py#L320>`_

   * - `COURSE_ENROLLMENT_CREATED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L48>`_
     - org.openedx.learning.course.enrollment.created.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/common/djangoapps/student/models.py#L1671>`_

   * - `COURSE_ENROLLMENT_CHANGED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L60>`_
     - org.openedx.learning.course.enrollment.changed.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/common/djangoapps/student/models.py#L1430>`_

   * - `COURSE_UNENROLLMENT_COMPLETED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L72>`_
     - org.openedx.learning.course.unenrollment.completed.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/common/djangoapps/student/models.py#L1457>`_

   * - `CERTIFICATE_CREATED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L84>`_
     - org.openedx.learning.certificate.created.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/certificates/models.py#L514>`_

   * - `CERTIFICATE_CHANGED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L94>`_
     - org.openedx.learning.certificate.changed.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/certificates/models.py#L482>`_

   * - `CERTIFICATE_REVOKED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L108>`_
     - org.openedx.learning.certificate.revoked.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/certificates/models.py#L402>`_

   * - `COHORT_MEMBERSHIP_CHANGED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L120>`_
     - org.openedx.learning.cohort_membership.changed.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/course_groups/models.py#L166>`_

   * - `COURSE_DISCUSSIONS_CHANGED <https://github.com/eduNEXT/openedx-events/blob/main/openedx_events/learning/signals.py#L132>`_
     - org.openedx.learning.discussions.configuration.changed.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/discussions/tasks.py#L30>`_


Content Authoring Events
^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 35 50 20

   * - *Name*
     - *Type*
     - *Date added*

   * - `COURSE_CATALOG_INFO_CHANGED <https://github.com/openedx/openedx-events/blob/main/openedx_events/content_authoring/signals.py#L23>`_
     - org.openedx.content_authoring.course.catalog_info.changed.v1
     - `2022-08-24 <https://github.com/openedx/edx-platform/blob/a8598fa1fac5e26ac212aa588e8527e727581742/cms/djangoapps/contentstore/signals/handlers.py#L111>`_

   * - `XBLOCK_PUBLISHED <https://github.com/openedx/openedx-events/blob/main/openedx_events/content_authoring/signals.py#L30>`_
     - org.openedx.content_authoring.xblock.published.v1
     - `2022-12-06 <https://github.com/openedx/edx-platform/blob/master/xmodule/modulestore/mixed.py#L926>`_

   * - `XBLOCK_DELETED <https://github.com/openedx/openedx-events/blob/main/openedx_events/content_authoring/signals.py#L42>`_
     - org.openedx.content_authoring.xblock.deleted.v1
     - `2022-12-06 <https://github.com/openedx/edx-platform/blob/master/xmodule/modulestore/mixed.py#L804>`_

   * - `XBLOCK_DUPLICATED <https://github.com/openedx/openedx-events/blob/main/openedx_events/content_authoring/signals.py#L54>`_
     - org.openedx.content_authoring.xblock.duplicated.v1
     - `2022-12-06 <https://github.com/openedx/edx-platform/blob/master/cms/djangoapps/contentstore/views/item.py#L965>`_
