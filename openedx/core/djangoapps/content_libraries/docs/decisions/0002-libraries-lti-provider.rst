Allow content libraries to be used by LTI consumers
---------------------------------------------------

Status
------

Pending

Context
-------

Currently, there's no way for xblocks in blockstore-based content libraries to be served to other LTI consumers. This ADR explores ways in which this can be achieved, without overly complicating the codebase. The platform currently does have an :code:`lms.lti_provider` app which implements the LTI 1.1 spec, but it only works for modulestore-based courses, and the LTI 1.1 spec itself is also deprecated and deemed insecure.

Decision
--------

We will use the latest LTI spec (`LTI 1.3`_) to serve the xblocks. This would be independent of the existing LTI 1.1 implementation, and will not require any changes in that app.

Instead, we will add additional code to :code:`openedx.core.content_libraries` application to handle LTI endpoints and communicate with the LTI consumers. We will use the actively-maintained `pylti1.3`_ package which can handle the LTI-spec implementation, which saves a lot of development and testing effort, and keeps the platform codebase relevant to openedx. The library is maintained by `@dmitry-viskov`_, who also proposed using it in an `earlier PR`_ to add LTI 1.3 support for courses. `pylti1.3`_ exists as an up-to-date `PyPi package`_, and is also used by projects like `my-learning-analytics`_, and `NimbleWise (source)`_.

Only two aspects of the LTI 1.3 spec family will be supported: Resource link launches and Assignment and Grading Services. Additional aspects of the implementation will not be supported, in particular, `LTI NRPS`_ and Deep Linking. Although they provide value for customers, we will focus on leaving the door open for them in the future.

The rest of the functionality would be similar to how the current LTI 1.1 provider works, having similar authentication, setup, and grade syncing, except for any changes required for the LTI 1.3 protocol. However, the new endpoints would be specific to blockstore-based content libraries and would not directly interact with modulestore-courses in any form. LTI platform launch authorization will rely on an association between the LTI platform and libraries exclusively. Multiple LTI platforms can be associated with multiple libraries. Site operators will manage this M:N relationship through the admin interface.

.. _LTI 1.3: http://www.imsglobal.org/activity/learning-tools-interoperability
.. _LTI NRPS: https://www.imsglobal.org/spec/lti-nrps/v2p0
.. _pylti1.3: https://github.com/dmitry-viskov/pylti1.3
.. _@dmitry-viskov: https://github.com/dmitry-viskov
.. _earlier PR: https://github.com/openedx/edx-platform/pull/21435
.. _PyPi package: https://pypi.org/project/PyLTI1p3/
.. _my-learning-analytics: https://github.com/tl-its-umich-edu/my-learning-analytics
.. _NimbleWise (source): https://github.com/openedx/edx-platform/pull/21435#issuecomment-664674601


Consequences
------------

Once implemented, content from blockstore-based libraries can be easily embedded into other LMS platforms. This is made easier by the fact that these libraries are designed to be embeddable, and can be easily rendered inside iframes. The library content can be used independently of courseware, are independent from course enrollments, and supports grading outside courses.  Including the ability to forward learner scoring via LTI.

Regarding authentication, the LTI 1.1 application creates dedicated users and associates them with LTI launches. This implementation will follow the same design. It means the same implications are also applied. In particular, the possibility of the users accessing other parts of the Open EdX instance besides the launched content through LTI.  We don't expect any impact on functionality by this.

Finally, the authorization model is orthogonal to the library permissions or authorization flags, enabling site operators to allow content libraries to serve LTI content independently. But, all LTI launches from the authorized platforms will be allowed.
