Status: Maintenance

Responsibilities
================
The Programs app is responsible (along with the `credentials app`_)
for communicating with the `credentials service`_, which is
the system of record for a learner's Program Certificates, and which (when enabled by the edX
instance) is the system of record for accessing all of a learner's credentials.

It also hosts program discussion forum and program live configuration.

.. _credentials service: https://github.com/openedx/credentials

.. _credentials app: https://github.com/openedx/edx-platform/tree/master/openedx/core/djangoapps/credentials

See Also
========

* ``lms/djangoapps/learner_dashboard/``,  which hosts the program dashboard.
* ``openedx/core/djangoapps/credentials``

