Optimizing Performance of All Course Dates API
=====================================================================

Status
------
Proposed

Context
-------

We encountered a performance issue while implementing an API for retrieving all course
dates for a specific user. This API is required for the mobile application to display
dates on the "Dates" tab, including the ability to shift due dates.

After implementation we noticed significant performance degradation when users
were enrolled in large courses containing numerous blocks. The function:

.. code-block:: python

    get_course_date_blocks(course, user, request, include_access=True, include_past_dates=True)

took more than one second to return data for a single course in these cases.
When multiple such courses were present, the API response time became unacceptably slow.

Problem Statement
-----------------
The current implementation of retrieving course dates dynamically by iterating through all
course blocks is inefficient for large courses. As the number of blocks increases, the API
response time grows significantly, leading to poor performance and a degraded user experience
in the mobile application. A more optimized approach is needed to ensure efficient data retrieval
while maintaining access checks.

Additionally, the existing models from `edx-when` do not fully meet our requirements. For example,
`ContentDate` does not contain the fields `first_component_block_id` and `assignment_title`.
As a result, we need to make multiple calls to modulestore to gather this data, which further
exacerbates the performance issues.


Decision
--------

To optimize performance, we decided to introduce a new model, `DateBlockInfo`, which will:

*   Have a foreign key to ContentDate.
*   Include additional fields such as `first_component_block_id` and `assignment_title`.
*   Be populated whenever a course is published, using the `SignalHandler.course_published` signal to iterate over
    all blocks and create instances of this model.
*   Be leveraged in the All Course Dates API to fetch instances associated with the user and perform access checks efficiently.

Consequences
------------

Positive:

*   Significantly improved API response times by precomputing and storing date-related information.
*   Reduced the need to traverse all blocks dynamically, improving scalability.
*   Ensured that access checks remain efficient and reliable.

Negative:

*   Additional storage space required for `DateBlockInfo` entries.
*   Extra processing during course publishing due to model instance creation.

This approach balances performance and maintainability, ensuring a better user experience in the mobile application while keeping data access efficient.
