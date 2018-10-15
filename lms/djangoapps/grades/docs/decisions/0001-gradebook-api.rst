1. Gradebook read and write APIs
--------------------------------

Status
======

Accepted

Context
=======

We are implementing a "Writable Gradebook" feature from the instructor dashboard.
This feature supports both the reading of subsection grades (e.g. for HW assignments, Labs, Exams)
and the creation/modification of subsection grades from a user interface.  This document captures
decisions related to the design of the Django APIs that support this feature.  This feature is heavily
inspired by an implementation provided by Extension Engine (EE).

Decisions
=========

#. **Feature-gating**

   a. This feature will be gated behind a `CourseWaffleFlag`.  This will allow us to roll out to a few courses
      as a time and to defer decisions that may need to be made about the scalability of this feature when
      applied to courses with a massive number (i.e. hundreds of thousands) of enrollments.  We can eventually
      remove the check for this flag.  When the flag is not enabled for a course, the endpoints will provide a
      response and status code indicating as much.

#. **The read (GET) API**

   a. The read API supports either fetching subsection scores for a single user, by `username`, or fetching
      a paginated result of subsection grade data for all enrollees in the requested course.

   b. We will use the data schema required by the EE's front-end implementation.  This will allow us to port
      over much of EE's front-end code with only minor modifications.  Note that there are some fields specified
      in EE's schema that will not be needed in the edX implementation, and we may remove those fields in future
      versions of this API.

   c. We will use the Django Rest Framework `CursorPagination` class as the base pagination class for all students' data
      in a course.  The query set that we paginate is the set of active enrollees for the requested course.  As a result
      of using this pagination class, paginated responses will not contain a `count` key, and the pagination query
      parameter `cursor` will have very opaque values.  Furthermore, due to the version of DRF installed in edx-platform,
      there is no available page size parameter available to clients of this API (although this can easily be added
      to our pagination class).

   d. The same pagination class as above is used as the pagination class for the `CourseGradesView` API.  This is for
      consistency, and also so that responses from this endpoint will be properly paginated (they previously contained
      only the paginated data, and relied on the client "knowing" that further pages were available by using the
      `?page=N` query parameter).

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
      requested items succeed, a ``202 (accepted)`` is returned.  This status code was chosen because an
      asynchronous celery task is enqueued for each subsection grade that needs to be updated.

   e. We have to thread a ``force_update_subsections`` keyword argument through the Django signal invocation
      that enqueues the subsection update task.  This is because we may be creating a new subsection grade
      with no score data available from either ``courseware.StudentModule`` records or from the `Submissions` API.
      In this case, the only score data available exists in the grade override record, and the subsection ``update()``
      call should be forced to read from this record.
