Status: Maintenance

Responsibilities
================
The Programs app is responsible for:

* Communicating with the `credentials service`_ (along with the `credentials app`_).
* Program discussion forum and program live configuration.
* The REST API used to render the program dashboard.  Legacy routes for this API, left over
  from the deprecated remnants of the legacy learner dashboard, exist alongside future-proofed
  routes which will work when the deprecated, legacy Program Dashboard is replaced with functionality
  in the Learner Dashboard MFE.

See Also
========

* `course_discovery_`: The system of record for the definition of a program.
* `credentials service_`: The system of record for a learner's Program Certificates and Program Records.
* `learner_record_`: The MFE displaying Program Records to learners.
* `legacy learner_dashboard_`: The legacy front-end for the program dashboard.

.. _course_discovery: https://github.com/openedx/course-discovery/

.. _credentials app: https://github.com/openedx/edx-platform/tree/master/openedx/core/djangoapps/credentials

.. _credentials service: https://github.com/openedx/credentials

.. _legacy learner_dashboard: https://github.com/openedx/edx-platform/tree/master/lms/djangoapps/learner_dashboard

.. _learner_record: https://github.com/openedx/frontend-app-learner-record