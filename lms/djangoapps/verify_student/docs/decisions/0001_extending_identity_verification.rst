0001. Extending Identity Verification
#####################################

Status
******

**Accepted** *2024-08-26*

Context
*******

The backend implementation of identity verification (IDV) is in the `verify_student Django application`_. The
`verify_student Django application`_ also contains a frontend user experience for performing photo IDV via an
integration with Software Secure. There is also a `React-based implementation of this flow`_ in the 
`frontend-app-account MFE`_, so the frontend user experience stored in the `verify_student Django application`_ is often
called the "legacy flow".

The current architecture of the `verify_student Django application`_ requires that any additional implementations of IDV
are stored in the application. For example, the Software Secure integration is stored in this application even though
it is a custom integration that the Open edX community does not use.

Different Open edX operators have different IDV needs. There is currently no way to add additional IDV implementations
to the platform without committing them to the core. The `verify_student Django application`_ needs enhanced
extensibility mechanisms to enable per-deployment integration of IDV implementations without modifying the core.

Decision
********

* We will support the integration of additional implementations of IDV through the use of Python plugins into the
  platform.
* We will add a ``VerificationAttempt`` model, which will store generic, implementation-agnostic information about an
  IDV attempt.
* We will expose a simple Python API to write and update instances of the ``VerificationAttempt`` model. This will
  enable plugins to publish information about their IDV attempts to the platform.
* The ``VerificationAttempt`` model will be integrated into the `verify_student Django application`_, particularly into
  the `IDVerificationService`_.
* We will emit Open edX events for each status change of a ``VerificationAttempt``.
* We will add an Open edX filter hook to change the URL of the photo IDV frontend.

Consequences
************

* It will become possible for Open edX operators to implement and integrate any additional forms of IDV necessary for
  their deployment.
* The `verify_student Django application`_ will contain both concrete implementations of forms of IDV (i.e. manual, SSO,
  Software Secure, etc.) and a generic, extensible implementation. The work to deprecate and remove the Software Secure
  integration and to transition the other existing forms of IDV (i.e. manual and SSO) to Django plugins will occur
  independently of the improvements to extensibility described in this decision.

Rejected Alternatives
*********************

We considered introducing a ``fetch_verification_attempts`` filter hook to allow plugins to expose additional
``VerificationAttempts`` to the platform in lieu of an additional model. However, doing database queries via filter
hooks can cause unpredictable performance problems, and this has been a pain point for Open edX.

References
**********
`[Proposal] Add Extensibility Mechanisms to IDV to Enable Integration of New IDV Vendor Persona <https://openedx.atlassian.net/wiki/spaces/OEPM/pages/4307386369/Proposal+Add+Extensibility+Mechanisms+to+IDV+to+Enable+Integration+of+New+IDV+Vendor+Persona>`_
`Add Extensibility Mechanisms to IDV to Enable Integration of New IDV Vendor Persona <https://github.com/openedx/platform-roadmap/issues/367>`_

.. _frontend-app-account MFE: https://github.com/openedx/frontend-app-account
.. _IDVerificationService: https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/verify_student/services.py#L55
.. _React-based implementation of this flow: https://github.com/openedx/frontend-app-account/tree/master/src/id-verification
.. _verify_student Django application: https://github.com/openedx/edx-platform/tree/master/lms/djangoapps/verify_student
