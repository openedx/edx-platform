1. Move Due Dates to Relational Database
----------------------------------------

Status
------

Proposed

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
    + ``ContentDate``: mapping content ids to dates
    + ``UserContentDate``: mapping user ids to ``ContentDates``. It will also record an audit trail for the override.
- The app will contain a custom XBlock field that will be a drop-in replacement for the existing Date XBlock field.
    + If the date exists in the relational database (whether in UserContentDate or ContentDate), it'll use that date; otherwise, it'll use the one stored in the XBlock.
- The app will expose a REST API for retrieving and updating dates in the database.

2. Create an instructor interface for setting student due dates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The existing IDDE instructor interface may be used, or a modern micro-frontend can be included from the new pluggable Django app.

3. All dates for a course/learner will be retrieved using one query, cached for the current request.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It's important that the underlying implementation can efficiently retrieve all due dates for the course, otherwise it's not an improvement over IDDE.

4. All new courses will automatically start storing due dates in the database.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since the new XBlock field will transparently convert dates between the content store and relational database, importing and exporting courses should automatically work. If not, an explicit import/export step may be needed. 

5. There may be a migration process for copying due date data from old courses into the new table.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the due date extension feature is desired for older courses, the due dates will need to be migrated by iterating the course blocks and copying dates into the database.


