Emit course completion event from edX platform
==============================================

Status
------

Pending

Context
-------

edX's implementation of xAPI emits course completion events. In order to replace the existing implementation with ``event-routing-backends``, we need to emit course completion events from edx platform. These events will then be transformed into desired specification (xAPI or Caliper) by ``event-routing-backends``.

Decision
--------

Events named ``edx.course.completed`` will be emitted from edx platform upon completion of a course. This event will contain the same fields as ``edx.course.enrollment.activated`` except for ``enterprise_uuid``.
