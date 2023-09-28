Emit course completion events from edX platform
===============================================

Status
------

Pending

Context
-------

#. edX's implementation of xAPI emits course completion event when learner passes a course. Having passed the course once, learners can still fail and pass the same course if they attempt the course content again or if the grading criteria changes.

#. edX's implementation of xAPI ensures that course completion event for a specific learner and course is emitted only once i.e. the first time this learner passes the course.

#. In order to replace the existing implementation, we need edX platform to emit a course completion event only once i.e. when the first time a learner passes a course.

Decision
--------

#. edX platform will be configured to emit an event named ``edx.course.grade.passed.first_time`` when a learner passes a course for the first time. This event will therefore be emitted when the learner has achieved passing grade AND passing timestamp of grade for this learner and course does not exist as seen `here`_.

#. For LRS consumers who may be interested in knowing whenever a learner passes or fails a course, edX platform will be configured to emit events named ``edx.course.grade.now_passed`` and ``edx.course.grade.now_failed``.
