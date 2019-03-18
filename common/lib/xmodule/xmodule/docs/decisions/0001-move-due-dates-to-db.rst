1. Move Due Dates to Relational Database
----------------------------------------

Status
------

Accepted

Context
-------

We want an authoritative and readily-accessible place to track due dates for sections/units in a course.  We also want to override due dates per learner, and record the reason for the override. The current implementation stores due dates in the XBlock (in mongodb). If you want to know all of the due dates in a course, you have to walk the entire course structure and pull out each date, which is an inefficient operation.

There is currently a way to override due dates per learner, using `IDDE <https://github.com/mitodl/ccx-idde-overrides-slides/blob/master/markdown/slides.md#individual-due-date-extensions-idde>`_, but this relies on a generic field-override system which doesn't know anything about the underlying data, and enabling this feature results in a database query for every xblock access, for every course on the platform. IDDE also does not allow for an audit trail on due date extensions, nor does it allow instructors to record a reason for the extension. 


Decisions
---------

1. Create a new pluggable Django app responsible for dates and date overrides
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This approach anticipates other date-related functions in the future, such as APIs for returning a calendar view of upcoming dates.

- The app will contain at least these models:
    + ``DatePolicy``: contains course_key, absolute date and a time delta
    + ``ContentDate``: contains DatePolicy id and content id + field
    + ``UserDate``: contains user id, DatePolicy id, and absolute date + relative date. It will also record an audit trail for the override.
- The app will hook in to the ``LmsModuleSystem`` with a custom ``FieldData`` implementation.
    + If the date exists in the relational database (whether in UserDate or ContentDate), it'll use that date; otherwise, it'll use the one stored in the XBlock.
- The app will expose a REST API for retrieving and updating dates in the database.

2. Create an instructor interface for setting student due dates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The existing IDDE instructor interface may be used, or a modern micro-frontend can be included from the new pluggable Django app.

3. All dates for a course/learner will be retrieved using one query, cached for the current request.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It's important that the underlying implementation can efficiently retrieve all due dates for the course, otherwise it's not an improvement over IDDE.

For instance, to retrieve all dates for a given user and course

::

    select cd.location, datep.date, datep.delta, ud.date, ud.delta
    from content_date cd
    left join date_policy datep on datep.id = cd.policy_id
    left join user_date ud on ud.policy_id = datep.id
    order by cd.location, ud.date, ud.delta
    where datep.course_key = "course_key"
    and ud.user_id = 1234


4. Dates will be copied to the relational database when the course is published.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The app will listen for the ``SignalHandler.course_published`` signal in Studio and will create/modify ``DatePolicies`` and ``ContentDates`` as required.

