1. Add External ID mapping in course overview
-----------------------------------

Status
------

Accepted

Context
-------

The Need for storing an external ID for a course run in edx platform primarily
comes from BootCamps. Bootcamp class objects are created in Salesforce
and have a class ID that is specific to Bootcamps ecosystem. Corresponding
course runs are automatically created in Canvas and store this class ID
in the field called sis_id.
Tools in BootCamps ecosystem leverage this sis_id to exchange information with
Canvas. This ID will potentially be used by multiple Bootcamp tools such as
Attendance, Central grading etc. So it should not be in a configuration
interface specific to any one tool.
This external ID is not limited to Bootcamp and can potentially be used for
integrating other systems into the edx platform.

Decision
--------

Adding this new external id mapping in the CourseOverview modal since that
model contains all the basic information of a course and allows this id to
be used by all areas of the edx-platform
