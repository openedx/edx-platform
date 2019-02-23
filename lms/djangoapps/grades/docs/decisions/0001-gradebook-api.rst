Gradebook read and write APIs
-----------------------------

Status
======

Accepted

Context
=======

We are implementing a "Writable Gradebook" feature from the instructor dashboard.
This feature supports both the reading of subsection grades (e.g. for HW assignments, Labs, Exams)
and the creation/modification of subsection grades from a user interface.  This document captures
decisions related to the design of the Django APIs that support this feature.

Decisions
=========

#. **Feature-gating**

   a. This feature will be gated behind a `CourseWaffleFlag`.  This will allow us to roll out to a few courses
      as a time and to defer decisions that may need to be made about the scalability of this feature when
      applied to courses with a massive number (i.e. hundreds of thousands) of enrollments.  We can eventually
      remove the check for this flag.  When the flag is not enabled for a course, the endpoints will provide a
      response and status code indicating as much.

#. **The read (GET) API**

   a. The read API supports either fetching subsection scores for a single user via ``?username=my-user-name``,
      where we look up a user by their exact ``username`` value; via ``?username_contains=name-substring`` where
      we do a case-insensitive substring query for a user, or fetching a paginated result of
      subsection grade data for all enrollees in the requested course.

   b. The schema of results includes information about the overall course grade as well as a "breakdown"
      of user grades for each graded subsection in the course.  The schema provides data needed by the client-side
      code; the client-side code is in charge of determining how to display that data (e.g. how many decimal
      places to round a percentage to).

   c. We will use the Django Rest Framework `CursorPagination` class as the base pagination class for all students' data
      in a course.  The query set that we paginate is the set of active enrollees for the requested course.  As a result
      of using this pagination class, paginated responses will not contain a `count` key, and the pagination query
      parameter `cursor` will have very opaque values.  We have added a ``get_page_size`` method to this
      class to allow clients to specify how many user results they would like in one page of data.

   d. The same pagination class as above is used as the pagination class for the `CourseGradesView` API.  This is for
      consistency, and also so that responses from this endpoint will be properly paginated (they previously contained
      only the paginated data, and relied on the client "knowing" that further pages were available by using the
      `?page=N` query parameter).

   e. We follow the approach of instructor Grade Reports for determining user subsection grade data.
      We collect the entire course structure once at the begining of course grade iteration and use that structure
      for reading subsection grades of all users.  We do this for performance reasons; we explicitly avoid
      fetching user-specific course structures, which is a costly operation.  One implication of this is that,
      for a user with no persisted subsection grade, we cannot determine the true possible number of points
      in that subsection as it relates to that user; it's possible the subsection is not visible to the user, or
      that certain problem blocks within the subsection are not visible to the user.  Since we cannot determine
      this possible number of points, all subsection grades where no attempt has been made by the user
      are assigned an earned/possible ratio of ``0/0``.

#. **The write (POST) API**

   a. The write API will be a `bulk-update` endpoint that allows for the creation/modification of subsection
      grades for multiple users and sections in a single request.  This allows clients of the API to limit
      the number of network requests made and to more easily manage client-side data.

   b. The write API will act as a `create-or-update` endpoint.  That is, if a persistent subsection grade record
      does not currently exist for a given user/subsection that the client intends to update, part of the
      request involves creating a corresponding persistent subsection grade record in addition to creating an override
      associated with that grade.  We do this because our grading system makes an assumption that a subsection's
      grade value is 0 if no record for that subsection exists, and therefore, a client reading grade data
      cannot make a distinction if a given subsection grade is 0 because no attempt or record exists, or if
      there is a recorded score somewhere of zero.  This should be completely opaque to that client, and thus,
      we create a grade if necessary in this endpoint.

   c. We won't fail the entire request if one item in the batch data raises an exception.  Instead, we will
      report the status (as a boolean value) for each requested grade override item in the request back to the client,
      along with a reason for items that have ``success: false`` entry.

   d. A status code of ``422`` will be returned for requests that contain any failed item.  This allows a client
      to easily tell if any item in their request payload was problematic and needs special handling.  If all
      requested items succeed, a ``202 (accepted)`` is returned.  This status code was chosen because a
      celery task is enqueued and waited for each subsection grade that needs to be updated.

   e. We have to thread a ``force_update_subsections`` keyword argument into the subsection update task that
      we enqueue.  This is because we may be creating a new subsection grade with no score data available from 
      either ``courseware.StudentModule`` records or from the `Submissions` API. In this case, the only score
      data available exists in the grade override record, and the subsection ``update()`` call should be forced
      to read from this record.

   f. We have to synchronously update each grade record for each user in this endpoint. This means POST requests
      will be open long enough for the override to be created and for all course/subsection grades
      to be updated for each user. The primary consumer gradebook UI needs to display the updated grade
      result for all users, after update is complete. If we do update asynchronously, the gradebook UI
      won't know how to update the table with new values for affected users' grades.
      This is the lowest effort change to address the UI display problem. We will
      need to improve this mechanism as we continue to develop.
