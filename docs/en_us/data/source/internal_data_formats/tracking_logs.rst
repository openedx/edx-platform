.. _Tracking Logs:

######################
Tracking Logs
######################

This chapter provides reference information about the event data that is
delivered in data packages. Events are emitted by the server or the browser to
capture information about interactions with the courseware and the Instructor
Dashboard in the LMS, and are stored in JSON documents. In the data package,
event data is delivered in a log file.

The sections in this chapter describe:

* A :ref:`sample_events`.
* :ref:`common` that are included in the JSON document of every event.
* :ref:`Student_Event_Types` for interactions with the LMS outside of the
  Instructor Dashboard. 
* :ref:`Instructor_Event_Types` for interactions with the Instructor Dashboard
  in the LMS.

Student and instructor events are grouped into categories in this chapter. For
a list of events, see the :ref:`event_list`.


.. _sample_events:

*************************
Sample Event
*************************

A sample event from an edX.log file follows. The JSON documents that include
event data are delivered in a compact, machine-readable format that can be
difficult to read at a glance.

.. code-block:: json

    {"agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) 
    Chrome/30.0.1599.101 Safari/537.36", "context": {"course_id": "edx/AN101/2014_T1", 
    "module": {"display_name": "Multiple Choice Questions"}, "org_id": "edx", "user_id": 
    9999999}, "event": {"answers": {"i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_2_1": 
    "yellow", "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_4_1": ["choice_0", "choice_2"]}, 
    "attempts": 1, "correct_map": {"i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_2_1": 
    {"correctness": "incorrect", "hint": "", "hintmode": null, "msg": "", "npoints": null, 
    "queuestate": null}, "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_4_1": 
    {"correctness": "correct", "hint": "", "hintmode": null, "msg": "", "npoints": null, 
    "queuestate": null}}, "grade": 2, "max_grade": 3, "problem_id": "i4x://edx/AN101/problem/
    a0effb954cca4759994f1ac9e9434bf4", "state": {"correct_map": {}, "done": null, "input_state": 
    {"i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_2_1": {}, "i4x-edx-AN101-problem-
    a0effb954cca4759994f1ac9e9434bf4_4_1": {}}, "seed": 1, "student_answers": {}}, "submission": 
    {"i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_2_1": {"answer": "yellow", "correct": 
    false, "input_type": "optioninput", "question": "What color is the open ocean on a sunny day?", 
    "response_type": "optionresponse", "variant": ""}, "i4x-edx-AN101-problem-
    a0effb954cca4759994f1ac9e9434bf4_4_1": {"answer": ["a piano", "a guitar"], "correct": true, 
    "input_type": "checkboxgroup", "question": "Which of the following are musical instruments?", 
    "response_type": "choiceresponse", "variant": ""}}, "success": "incorrect"}, "event_source": 
    "server", "event_type": "problem_check", "host": "precise64", "ip": "NN.N.N.N", "page": "x_module", 
    "time": 2014-03-03T16:19:05.584523+00:00", "username": "AAAAAAAAAA"}

If you use a JSON formatter to "pretty print" this event, a version that is more readable is produced.

.. code-block:: json

 {
    "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36", 
    "context": {
        "course_id": "edx/AN101/2014_T1", 
        "module": {
            "display_name": "Multiple Choice Questions"
        }, 
        "org_id": "edx", 
        "user_id": 9999999
    }, 
    "event": {
        "answers": {
            "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_2_1": "yellow", 
            "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_4_1": [
                "choice_0", 
                "choice_2"
            ]
        }, 
        "attempts": 1, 
        "correct_map": {
            "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_2_1": {
                "correctness": "incorrect", 
                "hint": "", 
                "hintmode": null, 
                "msg": "", 
                "npoints": null, 
                "queuestate": null
            }, 
            "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_4_1": {
                "correctness": "correct", 
                "hint": "", 
                "hintmode": null, 
                "msg": "", 
                "npoints": null, 
                "queuestate": null
            }
        }, 
        "grade": 2, 
        "max_grade": 3, 
        "problem_id": "i4x://edx/AN101/problem/a0effb954cca4759994f1ac9e9434bf4", 
        "state": {
            "correct_map": {}, 
            "done": null, 
            "input_state": {
                "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_2_1": {}, 
                "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_4_1": {}
            }, 
            "seed": 1, 
            "student_answers": {}
        }, 
        "submission": {
            "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_2_1": {
                "answer": "yellow", 
                "correct": false, 
                "input_type": "optioninput", 
                "question": "What color is the open ocean on a sunny day?", 
                "response_type": "optionresponse", 
                "variant": ""
            },
            "i4x-edx-AN101-problem-a0effb954cca4759994f1ac9e9434bf4_4_1": {
                "answer": [
                    "a piano", 
                    "a guitar"
                ], 
                "correct": true, 
                "input_type": "checkboxgroup", 
                "question": "Which of the following are musical instruments?", 
                "response_type": "choiceresponse", 
                "variant": ""
            }
        }, 
        "success": "incorrect"
    }, 
    "event_source": "server", 
    "event_type": "problem_check", 
    "host": "precise64", 
    "ip": "NN.N.N.N", 
    "page": "x_module", 
    "time": "2014-03-03T16:19:05.584523+00:00", 
    "username": "AAAAAAAAAA"
 }

.. _common:

********************
Common Fields
********************

This section describes the JSON fields that are common to the schema
definitions of all events.

=====================
``agent`` Field
=====================

**Type:** string

**Details:** Browser agent string of the user who triggered the event. 

.. _context:

===================
``context`` Field
===================

**Type:** dict

**Details:** For all events, this field includes member fields that
identify:

* The ``course_id`` of the course that generated the event.
* The ``org_id`` of the organization that lists the course. 
* The ``user_id`` of the individual who is performing the action. 
  
When included, ``course_user_tags`` contains a dictionary with the key(s) and
value(s) from the ``user_api_usercoursetag`` table for the user. See
:ref:`user_api_usercoursetag`.

The member fields are blank if values cannot be determined. The ``context``
field can also contain additional member fields that apply to specific events
only: see the description for each type of event.

**History**: Added 23 Oct 2013; ``user_id`` added 6 Nov 2013. Other event
fields may duplicate this data. ``course_user_tags`` added 12 Mar 2014.

===================
``event`` Field
===================

**Type:** dict

**Details:** This field includes member fields that identify specifics of each
triggered event. Different member fields are supplied for different events: see
the description for each type of event.

========================
``event_source`` Field
========================

**Type:** string

**Details:** Specifies whether the triggered event originated in the browser or
on the server. The values in this field are:

* 'browser'
* 'server'
* 'task'

=====================
``event_type`` Field
=====================

**Type:** string

**Details:** The type of event triggered. Values depend on ``event_source``.

The :ref:`Student_Event_Types` and :ref:`Instructor_Event_Types` sections in
this chapter provide descriptions of each type of event that is included in
data packages. To locate information about a specific event type, see the
:ref:`event_list`.

===================
``host`` Field
===================

**Type:** string

**Details:** The site visited by the user, for example, courses.edx.org.

===================
``ip`` Field
===================

**Type:** string

**Details:** IP address of the user who triggered the event. 

===================
``page`` Field
===================

**Type:** string

**Details:** The '$URL' of the page the user was visiting when the event was
emitted.

===================
``session`` Field
===================

**Type:** string

**Details:** This 32-character value is a key that identifies the user's
session. All browser events and the server :ref:`enrollment<enrollment>` events
include a value for the session. Other server events do not include a session
value.

===================
``time`` Field
===================

**Type:** string

**Details:** Gives the UTC time at which the event was emitted in 'YYYY-MM-
DDThh:mm:ss.xxxxxx' format.

===================
``username`` Field
===================

**Type:** string

**Details:** The username of the user who caused the event to be emitted. This
string is empty for anonymous events, such as when the user is not logged in.

.. _Student_Event_Types:

****************************************
Student Events
****************************************

This section lists the events that are logged for interactions with the LMS
outside the Instructor Dashboard.

* :ref:`enrollment`

* :ref:`navigational`

* :ref:`video`

* :ref:`pdf`

* :ref:`problem`

* :ref:`forum_events`

* :ref:`ora2`

* :ref:`AB_Event_Types`

* :ref:`ora`

The descriptions that follow include what each event represents, the system
component it originates from, the history of any changes made to the event over
time, and any additional member fields that the ``context`` and ``event``
fields contain.

The value in the ``event_source`` field (see the :ref:`common` section above)
distinguishes between events that originate in the browser (in JavaScript) and
events that originate on the server (during the processing of a request).

.. _enrollment:

=========================
Enrollment Events
=========================

.. tracked_command.py

``edx.course.enrollment.activated`` and ``edx.course.enrollment.deactivated``
------------------------------------------------------------------------------

The server emits these events in response to course enrollment
activities completed by a student.

* When a student enrolls in a course, ``edx.course.enrollment.activated`` is
  emitted. On edx.org, this is typically the result of a student clicking
  **Register** for the course.

* When a student unenrolls from a course, ``edx.course.enrollment.deactivated``
  is emitted. On edx.org, this is typically the result of a student clicking
  **Unregister** for the course.

In addition, actions by instructors and course staff members also generate
enrollment events. For the actions that members of the course team complete
that result in these events, see :ref:`instructor_enrollment`.

**Event Source**: Server

**History**: These enrollment events were added on 03 Dec 2013.

``context`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details and Member Fields
   * - ``path``
     - string
     - The URL path that generated the event: '/change_enrollment'.
       **History**: Added 07 May 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``course_id``
     - string
     - **History**: Maintained for backward compatibility. As of 23 Oct 2013,
       replaced by the ``context`` ``course_id`` field. See the description of
       the :ref:`context`.
   * - ``user_id``
     - integer
     - Identifies the user who was enrolled or unenrolled. 
   * - ``mode``
     - string
     - 'audit', 'honor', 'verified'
   * - ``name``
     - string
     - Identifies the type of event: 'edx.course.enrollment.activated' or
       'edx.course.enrollment.deactivated'. **History**: Added 07 May 2014 to
       replace the ``event`` ``event_type`` field.
   * - ``session``
     - string
     - The Django session ID, if available. Can be used to identify events for
       a specific user within a session. **History**: Added 07 May 2014.

Example
--------

.. reviewers, is this example accurate wrt the new fields?

.. code-block:: json

    {
        "username": "AAAAAAAAAA",
        "host": "courses.edx.org",
        "event_source": "server",
        "event_type": "edx.course.enrollment.activated",
        "context": {
          "course_id": "edX\/DemoX\/Demo_Course",
          "org_id": "edX",
          "path": "/change_enrollment",
          "user_id": 9999999
        },
        "time": "2014-01-26T00:28:28.388782+00:00",
        "ip": "NN.NN.NNN.NNN",
        "event": {
          "course_id": "edX\/DemoX\/Demo_Course",
          "user_id": 9999999,
          "mode": "honor"
          "name": "edx.course.enrollment.activated",
          "session": a14j3ifhskngw0gfgn230g
        },
        "agent": "Mozilla\/5.0 (Windows NT 6.1; WOW64; Trident\/7.0; rv:11.0) like Gecko",
        "page": null
      }

``edx.course.enrollment.upgrade.clicked``
-----------------------------------------------

Students who enroll with a ``student_courseenrollment.mode`` of 'audit' or
'honor' in a course that has a verified certificate option see a **Challenge
Yourself** link for the course on their dashboards. The browser emits this
event when a student clicks this option, and the process of upgrading the
``student_courseenrollment.mode`` for the student to 'verified' begins. See
:ref:`student_courseenrollment`.

**Event Source**: Browser

**History**: Added 18 Dec 2013.

``context`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details and Member Fields
   * - ``mode``
     - string
     - Enrollment mode when the user clicked **Challenge Yourself**: 'audit' or
       'honor'.

``event`` **Member Fields**: None.
       
``edx.course.enrollment.upgrade.succeeded``
--------------------------------------------

The server emits this event when the process of upgrading a student's
``student_courseenrollment.mode`` from 'audit' or 'honor' to 'verified' is
complete.

**Event Source**: Server

**History**: Added 18 Dec 2013.

``context`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details and Member Fields
   * - ``mode``
     - string
     - Set to 'verified'.

``event`` **Member Fields**: None.

.. _navigational:

==============================
Navigational Events   
==============================

.. display_spec.coffee

The browser emits these events when a user selects a navigational control. 

* ``seq_goto`` is emitted when a user jumps between units in a sequence. 

* ``seq_next`` is emitted when a user navigates to the next unit in a sequence.

* ``seq_prev`` is emitted when a user navigates to the previous unit in a
  sequence.

**Component**: Sequence 

.. **Question:** what does a "sequence" correspond to in Studio? a subsection?

**Event Source**: Browser

``event`` **Member Fields**: 

All of the navigational events add the same fields to the ``event`` dict field:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``old``
     - integer
     - For ``seq_goto``, the index of the unit being jumped from. For
       ``seq_next`` and ``seq_prev``, the index of the unit being navigated away
       from.
   * - ``new``
     - integer
     - For ``seq_goto``, the index of the unit being jumped to. For ``seq_next``
       and ``seq_prev``, the index of the unit being navigated to. 
   * - ``id``
     - integer
     - The edX ID of the sequence. 

``page_close``
---------------

An additional type of event, ``page_close``, originates from within the
JavaScript Logger itself.

.. what is the function of the Logger? what value do the events that it logs have? is event_source by any chance set to 'task' for these?

**Component**: JavaScript Logger

**Event Source**: Browser

``event`` **Member Fields**: None

.. _video:

==============================
Video Interaction Events   
==============================

.. video_player_spec.js, lms-modules.js

The browser emits these events when a user works with a video.

**Component**: Video

**Event Source**: Browser

``play_video``, ``pause_video``
---------------------------------

* The browser emits ``play_video`` events when the user clicks the video
  **play** control.

* The browser emits  ``pause_video`` events when the user clicks the video
  **pause** control. The browser also emits these events when the video player
  reaches the end of the video file and play automatically stops.

``event`` **Member Fields**: These events have the same ``event`` fields.

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``id``
     - string
     - EdX ID of the video being watched (for example, i4x-HarvardX-PH207x-video-Simple_Random_Sample).
   * - ``code``
     - string
     - For YouTube videos, the ID of the video being loaded (for example,
       OEyXaRPEzfM). For non-YouTube videos, 'html5'.
   * - ``currentTime``
     - float
     - Time the video was played, in seconds. 
   * - ``speed``
     - string
     - Video speed in use: '0.75', '1.0', '1.25', '1.50'.

``stop_video``
--------------------

The browser emits  ``stop_video`` events when the video player reaches the end
of the video file and play automatically stops.

**History**: Added 25 June 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``currentTime``
     - float
     - Time the video ended, in seconds. 

``seek_video``
-----------------

The browser emits ``seek_video`` events when a user clicks the playback bar or
transcript to go to a different point in the video file.

**History**: Prior to 25 Jun 2014, the ``old_time`` and ``new_time`` were set
to the same value.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``old_time``
     - integer
     - The time in the video, in seconds, at which the user chose to go to a
       different point in the file.
   * - ``new_time``
     - integer
     - The time in the video, in seconds, that the user selected as the
       destination point.
   * - ``type``
     - string
     - The navigational method used to change position within the video.

``speed_change_video`` 
------------------------

The browser emits ``speed_change_video`` events when a user selects a different
playing speed for the video.

**History**: Prior to 12 Feb 2014, this event was emitted when the user
selected either the same speed or a different speed.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``current_time``
     - 
     - The time in the video that the user chose to change the playing speed.  
   * - ``old_speed``
     - 
     - The speed at which the video was playing. 
   * - ``new_speed``
     - 
     - The speed that the user selected for the video to play. 

``load_video``
-----------------

The browser emits  ``load_video`` events when the video is fully rendered and
ready to play.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``code``
     - string
     - For YouTube videos, the ID of the video being loaded (for example,
       OEyXaRPEzfM). For non-YouTube videos, 'html5'.

``hide_transcript``
-------------------

The browser emits  ``hide_transcript`` events when the user clicks **CC** to
suppress display of the video transcript.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``code``
     - string
     - For YouTube videos, the ID of the video being loaded (for example,
       OEyXaRPEzfM). For non-YouTube videos, 'html5'.
   * - ``currentTime``
     - float
     - The point in the video file at which the transcript was hidden, in seconds. 

``show_transcript``
--------------------

The browser emits  ``show_transcript`` events when the user clicks **CC** to
display the video transcript.


.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``code``
     - string
     - For YouTube videos, the ID of the video being loaded (for example,
       OEyXaRPEzfM). For non-YouTube videos, 'html5'.
   * - ``currentTime``
     - float
     - The point in the video file at which the transcript was opened, in seconds. 

.. _pdf:

=================================
Textbook Interaction Events   
=================================

.. pdf-analytics.js

``book``
----------

The browser emits ``book`` events when a user navigates within the PDF Viewer
or the PNG Viewer.

* For textbooks in PDF format, the URL in the common ``page`` field contains
  '/pdfbook/'.
* For textbooks in PNG format, the URL in the common ``page`` field contains
  '/book/'.

**Component**: PDF Viewer, PNG Viewer 

**Event Source**: Browser

**History**: This event changed on 16 Apr 2014 to include ``event`` member
fields ``name`` and ``chapter``.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``type``
     - string
     -  
       * 'gotopage' is emitted when a page loads after the student manually enters its number.
       * 'prevpage' is emitted when the next page button is clicked.
       * 'nextpage' is emitted when the previous page button is clicked.

   * - ``name``
     - string
     -  
       * For 'gotopage', set to ``textbook.pdf.page.loaded``.
       * For 'prevpage', set to ``textbook.pdf.page.navigatedprevious``. 
       * For 'nextpage', set to ``textbook.pdf.page.navigatednext``. 
       
       **History**: Added for events produced by the PDF Viewer on 16 Apr 2014.
   * - ``chapter``
     - string
     - The name of the PDF file. 
       **History**: Added for events produced by the PDF Viewer on 16 Apr 2014.
   * - ``old``
     - integer
     - The original page number. Applies to 'gotopage' event types only.   
   * - ``new``
     - integer
     - Destination page number.

``textbook.pdf.thumbnails.toggled``
------------------------------------

The browser emits ``textbook.pdf.thumbnails.toggled`` events when a user clicks
on the icon to show or hide page thumbnails.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.thumbnails.toggled``
   * - ``chapter``
     -  string
     -  The name of the PDF file.
   * -  ``page``
     -  integer
     -  The number of the page that is open when the user clicks this icon. 

``textbook.pdf.thumbnail.navigated``
------------------------------------

The browser emits ``textbook.pdf.thumbnail.navigated`` events when a user
clicks on a thumbnail image to navigate to a page.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.thumbnail.navigated``
   * - ``chapter`` 
     - string
     - The name of the PDF file. 
   * - ``page``
     - integer
     - The page number of the thumbnail clicked.
   * - ``thumbnail_title``
     - string
     - The identifying name for the destination of the thumbnail. For example, Page 2. 

``textbook.pdf.outline.toggled``
------------------------------------

The browser emits ``textbook.pdf.outline.toggled`` events when a user clicks
the outline icon to show or hide a list of the book's chapters.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.outline.toggled``
   * - ``chapter`` 
     - string
     - The name of the PDF file.
   * - ``page`` 
     - integer
     - The number of the page that is open when the user clicks this link.

``textbook.pdf.chapter.navigated``
------------------------------------

The browser emits ``textbook.pdf.chapter.navigated`` events when a user clicks
on a link in the outline to navigate to a chapter.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.chapter.navigated``
   * - ``chapter``
     - string
     - The name of the PDF file.
   * - ``chapter_title``
     - string
     - The identifying name for the destination of the outline link. 
     
``textbook.pdf.page.navigated``
------------------------------------

The browser emits ``textbook.pdf.page.navigated`` events when a user manually
enters a page number.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.page.navigated``
   * - ``chapter``
     - string
     - The name of the PDF file.
   * - ``page``
     - integer
     - The destination page number entered by the user.

``textbook.pdf.zoom.buttons.changed``
--------------------------------------

The browser emits ``textbook.pdf.zoom.buttons.changed`` events when a user
clicks either the Zoom In or Zoom Out icon.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.zoom.buttons.changed``
   * - ``direction``
     -  string
     -  'in', 'out'
   * - ``chapter``
     - string
     - The name of the PDF file.
   * - ``page``
     - integer
     - The number of the page that is open when the user clicks the icon.

``textbook.pdf.zoom.menu.changed``
------------------------------------

The browser emits ``textbook.pdf.zoom.menu.changed`` events when a user selects
a magnification setting.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.zoom.menu.changed``
   * - ``amount``
     - string
     - '1', '0.75', '1.5', 'custom', 'page_actual', 'auto', 'page_width', 'page_fit'.
   * - ``chapter``
     - string
     - The name of the PDF file.
   * - ``page``
     - integer
     - The number of the page that is open when the user selects this value.

``textbook.pdf.display.scaled``
------------------------------------

The browser emits ``textbook.pdf.display.scaled`` events when the display
magnification changes. These changes occur after a student selects a
magnification setting from the zoom menu or resizes the browser window.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.display.scaled``
   * - ``amount``
     - string
     - The magnification setting; for example, 0.95 or 1.25.
   * - ``chapter``
     - string
     - The name of the PDF file. 
   * - ``page`` 
     - integer
     - The number of the page that is open when the scaling takes place.

``textbook.pdf.display.scrolled``
------------------------------------

The browser emits ``textbook.pdf.display.scrolled`` events each time the
displayed page changes while a user scrolls up or down.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.display.scrolled``
   * - ``chapter``
     - string
     - The name of the PDF file. 
   * - ``page``
     - integer
     - The number of the page that is open when the scrolling takes place.
   * - ``direction``
     - string
     - 'up', 'down' 

``textbook.pdf.search.executed``
------------------------------------

The browser emits ``textbook.pdf.search.executed`` events when a user searches
for a text value in the file. To reduce the number of events produced, instead
of producing one event per entered character this event defines a search string
as the set of characters that is consecutively entered in the search field
within 500ms of each other.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1


   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.search.executed``
   * - ``query``
     - string
     - The value in the search field.
   * - ``caseSensitive``
     - boolean
     - 'true' if the case sensitive option is selected, 'false' if this option is not selected.
   * - ``highlightAll``
     - boolean
     - 'true' if the option to highlight all matches is selected, 'false' if this option is not selected.
   * - ``status``
     - string
     - A "not found" status phrase for a search string that is unsuccessful. Blank for successful search strings.
   * - ``chapter``
     - string
     - The name of the PDF file. 
   * - ``page``
     - integer
     - The number of the page that is open when the search takes place.

``textbook.pdf.search.navigatednext``
---------------------------------------------

The browser emits ``textbook.pdf.search.navigatednext`` events when a user
clicks on the Find Next or Find Previous icons for an entered search string.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.search.navigatednext`` 
   * - ``findprevious``
     - boolean
     - 'true' if the user clicks the Find Previous icon, 'false' if the user clicks the Find Next icon.
   * - ``query``
     - string
     - The value in the search field.
   * - ``caseSensitive``
     - boolean
     - 'true' if the case sensitive option is selected, 'false' if this option is not selected.  
   * - ``highlightAll``
     - boolean
     - 'true' if the option to highlight all matches is selected, 'false' if this option is not selected. 
   * - ``status``
     -  string
     - A "not found" status phrase for a search string that is unsuccessful. Blank for successful search strings.   
   * - ``chapter``
     - string
     - The name of the PDF file. 
   * - ``page``
     - integer
     - The number of the page that is open when the search takes place.

``textbook.pdf.search.highlight.toggled``
---------------------------------------------

The browser emits ``textbook.pdf.search.highlight.toggled`` events when a user
selects or clears the **Highlight All** option for a search.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.search.highlight.toggled``
   * - ``query``
     - string
     - The value in the search field. 
   * - ``caseSensitive``
     - boolean
     - 'true' if the case sensitive option is selected, false' if this option is not selected. 
   * - ``highlightAll``
     - boolean
     - 'true' if the option to highlight all matches is selected, 'false' if this option is not selected.
   * - ``status``
     - string
     - A "not found" status phrase for a search string that is unsuccessful. Blank for successful search strings.
   * - ``chapter``
     - string
     - The name of the PDF file. 
   * - ``page``
     - integer
     - The number of the page that is open when the search takes place.

``textbook.pdf.search.casesensitivity.toggled``
------------------------------------------------------

The browser emits ``textbook.pdf.search.casesensitivity.toggled`` events when a
user selects or clears the **Match Case** option for a search.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event was added on 16 Apr 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``name``
     - string
     - ``textbook.pdf.search.casesensitivity.toggled``
   * - ``query``
     - string
     - The value in the search field.
   * - ``caseSensitive``
     - boolean
     - 'true' if the case sensitive option is selected, 'false' if this option is not selected.
   * - ``highlightAll``
     - boolean
     - 'true' if the option to highlight all matches is selected, 'false' if this option is not selected. 
   * - ``status``
     -  string
     - A "not found" status phrase for a search string that is unsuccessful. Blank for successful search strings.
   * - ``chapter``
     - string
     - The name of the PDF file. 
   * - ``page``
     - integer
     - The number of the page that is open when the search takes place.

.. _problem:

=================================
Problem Interaction Events 
=================================

.. lms-modules.js These events are Capa Module

Problem interaction events are emitted by the server or the browser to capture
information about interactions with problems, specifically, problems defined in
the edX Capa module.

``problem_check`` (Browser)
----------------------------

.. no sample to check

Both browser interactions and server requests produce ``problem_check`` events.
The browser emits ``problem_check`` events when a user checks a problem.

**Event Source**: Browser 

``event`` **Member Fields**: For browser-emitted ``problem_check`` events, the
``event`` field contains the values of all input fields from the problem being
checked, styled as GET parameters.

``problem_check`` (Server)
----------------------------

.. no sample to check

Both browser interactions and server requests produce ``problem_check`` events.

The server emits ``problem_check`` events when a problem is successfully
checked.
  
**Event Source**: Server

**History**: 

* On 5 Mar 2014, the ``submission`` dictionary was added to the ``event`` field
  and  ``module`` was added to the ``context`` field.

* Prior to 15 Oct 2013, this server-emitted event was named
  ``save_problem_check``.

* Prior to 15 Jul 2013, this event was emitted twice for the same action.

``context`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``module``
     - dict
     - Provides the specific problem component as part of the context. Contains
       the member field ``display_name``, which is the string value for the
       **Display Name** given to the problem component.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``answers``
     - dict
     - The problem ID and the internal answer identifier in a name:value pair.
       For a component with multiple problems, lists every problem and
       answer.
   * - ``attempts``
     - integer
     - The number of times the user attempted to answer the problem.
   * - ``correct_map``
     - dict
     - For each problem ID value listed by ``answers``, provides:
       
       * ``correctness``: string; 'correct', 'incorrect'
       * ``hint``: string; Gives optional hint. Nulls allowed. 
       * ``hintmode``: string; None, 'on_request', 'always'. Nulls allowed. 
       * ``msg``: string; Gives extra message response.
       * ``npoints``: integer; Points awarded for this ``answer_id``. Nulls allowed.
       * ``queuestate``: dict; None when not queued, else ``{key:'', time:''}``
         where ``key`` is a secret string dump of a DateTime object in the form
         '%Y%m%d%H%M%S'. Nulls allowed. 

   * - ``grade``
     - integer
     - Current grade value. 
   * - ``max_grade``
     - integer
     - Maximum possible grade value.
   * - ``problem_id``
     - string
     - ID of the problem that was checked.
   * - ``state``
     - dict
     - Current problem state.
   * - ``submission``
     - object
     - Provides data about the response made. For components that include
       multiple problems, a separate submission object is provided for each one.

       * ``answer``: string; The value that the student entered, or the display name of the value selected.
       * ``correct``: Boolean; 'true', 'false'
       * ``input_type``: string; The type of value that the student supplies for
         the ``response_type``. Based on the XML element names used in the
         Advanced Editor. Examples include 'checkboxgroup', 'radiogroup',
         'choicegroup', and 'textline'.
       * ``question``: string; Provides the text of the question.
       * ``response_type``: string; The type of problem. Based on the XML
         element names used in the Advanced  Editor. Examples include
         'choiceresponse', 'optionresponse', and 'multiplechoiceresponse'.
       * ``variant``: integer; For problems that use problem randomization
         features such as answer pools or choice shuffling, contains the unique
         ID of the variant that was presented to this user. 

   * - ``success``
     - string
     - 'correct', 'incorrect' 

``problem_check_fail``
-----------------------------

.. no sample to check

The server emits ``problem_check_fail`` events when a problem cannot be checked
successfully.

**Event Source**: Server

**History**: Prior to 15 Oct 2013, this event was named
``save_problem_check_fail``.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``state``  
     - dict
     - Current problem state.
   * - ``problem_id``
     - string
     - ID of the problem being checked.
   * - ``answers`` 
     - dict
     - 
   * - ``failure`` 
     - string
     - 'closed', 'unreset'

``problem_reset``
--------------------

The browser emits ``problem_reset`` events when a user clicks **Reset** to
reset the answer to a problem.

.. return Logger.log('problem_reset', [_this.answers, response.contents], _this.id);

**Event Source**: Browser

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``answers``
     - string
     - The value reset by the user. 

``problem_rescore``
-----------------------------

.. no sample to check

The server emits ``problem_rescore`` events when a problem is successfully
rescored.

**Event Source**: Server

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``state``
     - dict
     - Current problem state.
   * - ``problem_id``
     - string
     - ID of the problem being rescored.
   * - ``orig_score``
     - integer
     - 
   * - ``orig_total``
     - integer
     - 
   * - ``new_score`` 
     - integer
     - 
   * - ``new_total``
     - integer
     - 
   * - ``correct_map``
     - dict
     - See the fields for the ``problem_check`` server event above.
   * - ``success``
     - string
     - 'correct', 'incorrect'
   * - ``attempts``
     - integer
     - 

``problem_rescore_fail``
-----------------------------

.. no sample to check

The server emits ``problem_rescore_fail`` events when a problem cannot be
successfully rescored.

**Event Source**: Server

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``state``
     - dict
     - Current problem state. 
   * - ``problem_id``
     - string
     - ID of the problem being checked.
   * - ``failure`` 
     - string
     - 'unsupported', 'unanswered', 'input_error', 'unexpected'

``problem_save``
-----------------------------

.. no sample to check

The browser emits ``problem_save`` events when a user saves a problem.

**Event Source**: Browser

``event`` **Member Fields**: None

``problem_show``
-----------------------------

.. no sample to check

The browser emits ``problem_show`` events when a problem is shown.  

.. %%

**Event Source**: Browser

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``problem``
     - string
     - ID of the problem being shown. For example,
       i4x://MITx/6.00x/problem/L15:L15_Problem_2).

``reset_problem``
------------------------------------------------

.. no sample to check

The server emits ``reset_problem`` events when a problem has been reset
successfully.

.. %%what is the difference between reset_problem and problem_reset?

**Event Source**: Server

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``old_state``
     - dict
     - The state of the problem before the reset was performed. 
   * - ``problem_id``
     - string
     - ID of the problem being reset.
   * - ``new_state``
     - dict
     - New problem state.  

``reset_problem_fail`` 
------------------------------------------------

.. no sample to check

The server emits ``reset_problem_fail`` events when a problem cannot be reset
successfully.

**Event Source**: Server

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``old_state``
     - dict
     - The state of the problem before the reset was requested.
   * - ``problem_id``
     - string
     - ID of the problem being reset.  
   * - ``failure``
     - string
     - 'closed', 'not_done'

``show_answer`` 
------------------------------------------------

.. no sample to check

The server emits ``show_answer`` events when the answer to a problem is shown. 

**Event Source**: Server

**History**: The original name for this event was ``showanswer``. 

.. **Question** is this renaming info correct?

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``problem_id``
     - string
     - EdX ID of the problem being shown. 

``save_problem_fail`` 
------------------------------------------------

.. no sample to check

The server emits ``save_problem_fail``  events when a problem cannot be saved
successfully.

**Event Source**: Server

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``state``
     - dict
     - Current problem state.
   * - ``problem_id``
     - string
     - ID of the problem being saved. 
   * - ``failure`` 
     - string
     - 'closed', 'done' 
   * - ``answers`` 
     - dict
     - 

``save_problem_success`` 
------------------------------------------------

.. no sample to check

The server emits ``save_problem_success`` events when a problem is saved
successfully.

**Event Source**: Server

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``state``
     - dict
     - Current problem state. 
   * - ``problem_id``
     - string
     - ID of the problem being saved. 
   * - ``answers``
     -  dict
     -  

``problem_graded``
-------------------

.. return Logger.log('problem_graded', [_this.answers, response.contents], _this.id);

The server emits a ``problem_graded`` event each time a user clicks **Check**
for a problem and it is graded successfully.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``[answers, contents]``
     - array
     - ``answers`` provides the value checked by the user. ``contents``
       delivers HTML using data entered for the problem in Studio, including
       the display name, problem text, and choices or response field labels.
       The array includes each problem in a problem component that has multiple
       problems.

.. _forum_events:

==========================
Forum Events
==========================

``edx.forum.searched``
----------------------------------

After a user executes a text search in the navigation sidebar of the course
**Discussion** page, the server emits an ``edx.forum.searched`` event.

**Component**: Discussion

**Event Source**: Server

**History**: Added 16 May 2014.  The ``corrected_text`` field was added 5
Jun 2014.

``event`` **Fields**:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``query``
     - string
     - The text entered into the search box by the user.
   * - ``page``
     - integer
     - Results are returned in sets of 20 per page. Identifies the page of
       results requested by the user.
   * - ``total_results``
     - integer
     - The total number of results matching the query.
   * - ``corrected_text``
     - string
     - A re-spelling of the query, suggested by the search engine, which was
       automatically substituted for the original one.  This happens only when
       there are no results for the original query, but the index contains
       matches for a similar term or phrase.  Otherwise, this field is null.

.. _ora2:

======================================
Open Response Assessment Events 
======================================

In an open response assessment, students review a question and then submit a
text response and, optionally, an image file. To evaluate their own and one or
more other students' responses to the questions, students use an instructor-
definfed scoring rubric. For more information about open response assessments,
see `Creating a Peer Assessment`_.

**Component**: Open Response Assessments

**History:** The open response assessment feature was released in August 2014;
limited release of this feature began in April 2014.

openassessmentblock.get_peer_submission
----------------------------------------

After students submit their own responses for evaluation, they use the scoring
rubric to evaluate the responses of other course participants. The server emits
this event when a response is delivered to a student for evaluation.

**Event Source**: Server

**History**: Added 3 April 2014.

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``course_id``
     - string
     - The identifier of the course that includes this assessment. For open
       response assessment problems, the course ID is stated in org/course/run
       format. 

       (For courses created after mid-2014, the course ID is converted to this
       format for open response assessment problems only.)

   * - ``item_id``
     - string
     - The i4x:// style locator that identifies the problem in the course. 
   * - ``submission_returned_uuid``
     - string
     - The unique identifer of the response that the student retrieved for
       assessment. 

       If no assessment is available, this is set to "None".

   * - ``requesting_student_id``
     - string
     - The course-specific anonymized user ID of the student who requested the
       response.

       
openassessmentblock.peer_assess and openassessmentblock.self_assess
----------------------------------------------------------------------

The server emits this event when a student either submits an assessment of a
peer's response or submits a self-assessment of her own response.

**Event Source**: Server

**History**: Added 3 April 2014.

``event`` **Fields**:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``scorer_id``
     - string
     - The course-specific anonymized user ID of the student who submitted this
       assessment.
   * - ``feedback``
     - string
     - The student's comments about the submitted response.
   * - ``submission_uuid``
     - string
     - The unique identifier for the submitted response.
   * - ``score_type``
     - string
     - "PE" for a peer evaluation, "SE" for a self evaluation.
   * - ``parts: [criterion, option, feedback]``
     - array
     - The ``parts`` field contains member fields for each ``criterion`` in the
       rubric, the ``option`` that the student selected for it, and any
       ``feedback`` comments that the student supplied. 

       These member fields are repeated in an array to include all of the
       rubric's criteria.

       * ``criterion`` (object) contains ``points possible`` and ``name``
         member fields
       * ``option`` (string)
       * ``feedback`` (string)

       When the only criterion in the rubric is student feedback, ``points
       possible`` is 0 and the ``option`` field is not included.
       
   * - ``rubric``
     - dict
     - This field contains the member field ``contenthash``, which identifies
       the rubric that the student used to assess the response.
   * - ``scored_at``
     - datetime
     - Timestamp for when the assessment was submitted.

openassessmentblock.submit_feedback_on_assessments
----------------------------------------------------

The server emits this event when a student submits a suggestion, opinion, or
other feedback about the assessment process.

**Event Source**: Server

**History**: Added 3 April 2014.

``event`` **Fields**:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``feedback_text``
     - string
     - The student's comments about the assessment process.
   * - ``submission_uuid``
     - string
     - The unique identifier of the feedback.
   * - ``options``
     - array
     - The label of each check box option that the student selected to evaluate
       the assessment process.

openassessment.create_submission
--------------------------------

The server emits this event when a student submits a response. The same event
is emitted when a student submits a response for peer assessment or for self
assessment.

**Event Source**: Server

**History**: Added 3 April 2014.

``event`` **Fields**:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``answer``
     - dict
     - This field contains a ``text`` (string) member field for the response. 
       
       For responses that also include an image file, this field contains a
       ``file_upload_key`` (string) member field with the AWS S3 key that
       identifies the location of the image file on the Amazon S3 storage
       service. This key is provided for reference only.

   * - ``created_at``
     - datetime
     - Timestamp for when the student submitted the response.
   * - ``attempt_number``
     - int
     - This value is currently always set to 1.
   * - ``submission_uuid``
     - string
     - The unique identifier of the response.
   * - ``submitted_at``
     - datetime
     - Timestamp for when the student submitted the response. This value is
       currently always the same as ``created_at``.

openassessment.save_submission
-------------------------------

The server emits this event when a student saves a response. Students
save responses before they submit them for assessment.

**Event Source**: Server

**History**: Added 3 April 2014.

``event`` **Fields**:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``saved_response``
     - dict
     - This field contains a ``text`` (string) member field for the response. 
       
       For responses that also include an image file, this field contains a
       ``file_upload_key`` (string) member field with the AWS S3 key that
       identifies the location of the image file on the Amazon S3 storage
       service.

openassessment.student_training_assess_example
-----------------------------------------------

The server emits this event when a student submits an assessment for an
example response. To assess the example, the student uses a scoring rubric
provided by the instructor. These events record the options the student
selected to assess the example and identifies any criteria that the student
scored differently than the instructor.

**Event Source**: Server

**History**: Added 6 August 2014.

``event`` **Fields**:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``corrections``
     - object
     - A set of name/value pairs that identify criteria for which the student
       selected a different option than the instructor, in the format
       ``criterion_name: instructor-defined_option_name``.
   * - ``submission_uuid``
     - string
     - The unique identifier of the response. Identifies the student who
       is undergoing training.
   * - ``options_selected``
     - object
     - A set of name/value pairs that identify the option that the student
       selected for each criterion in the rubric, in the format
       ``'criterion_name': 'option_name'``.

openassessment.upload_file 
-----------------------------

The browser emits this event when a student successfully uploads an image file
as part of a response. Students complete the upload process before they submit
the response.

**Event Source**: Browser

**History**: Added 6 August 2014.

``event`` **Fields**:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``fileType``
     - string
     - The MIME type of the uploaded file. Reported by the student's browser.
   * - ``fileName``
     - string
     - The name of the uploaded file, as stored on the student's client
       machine.
   * - ``fileSize``
     - int
     - The size of the uploaded file in bytes. Reported by the student's
       browser.

.. _AB_Event_Types:

==========================
A/B Testing Events
==========================

Course authors can configure course content to present modules that contain
other modules. For example, a parent module can include two child modules with
content that differs in some way for comparison testing. When a student
navigates to a module that is set up for A/B testing in this way, the student
is randomly assigned to a group and shown only one of the child modules.

* Internally, a *partition* defines the type of experiment: comparing the
  effectiveness of video alone to text alone, for example. A course can include
  any number of modules with the same partition, or experiment type.

* For each partition, students are randomly assigned to a *group*. The group
  determines which content, either video or text in this example, is shown by
  every module with that partitioning.

The events that follow apply to modules that are set up to randomly assign
students to groups so that different content can be shown to the different
groups.

**History**: These events were added on 12 Mar 2014.

``assigned_user_to_partition``
----------------------------------

When a student views a module that is set up to test different child modules,
the server checks the ``user_api_usercoursetag`` table for the student's
assignment to the relevant partition, and to a group for that partition. 

* The partition ID is the ``user_api_usercoursetag.key``.

* The group ID is the ``user_api_usercoursetag.value``.

If the student does not yet have an assignment, the server emits an
``assigned_user_to_partition`` event and adds a row to the
``user_api_usercoursetag`` table for the student. See
:ref:`user_api_usercoursetag`.

.. note:: After this event is emitted, the common ``context`` field in all subsequent events includes a ``course_user_tags`` member field with the student's assigned partition and group.

**Component**: Split Test

**Event Source**: Browser

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``group_id``
     - integer
     - Identifier of the group.
   * - ``group_name``
     - string
     - Name of the group. 
   * - ``partition_id``
     - integer
     - Identifier for the partition, in the format
       ``xblock.partition_service.partition_ID`` where ID is an integer.
   * - ``partition_name``
     - string
     - Name of the partition.

``child_render``
----------------------------------

When a student views a module that is set up to test different content using
child modules, the server emits a ``child_render`` event to identify
the child module that was shown to the student.

**Component**: Split Test

**Event Source**: Server

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``child-id``
     - string
     - ID of the module that displays to the student. 

.. _ora:

============================================
Open Response Assessment Events (Deprecated)
============================================

**History**: The events in this section recorded interactions with the
prototype implementation of open response assessment (ORA) problem types. As of
May 2014, new courses no longer used this implementation for open response
assessments.

``oe_hide_question`` and ``oe_show_question``
---------------------------------------------------------------------------

The browser emits ``oe_hide_question`` and ``oe_show_question`` events when the
user hides or redisplays a combined open-ended problem.

**History**: These events were previously named ``oe_hide_problem`` and
``oe_show_problem``.

**Component**: Combined Open-Ended

**Event Source**: Browser

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``location``
     - string
     - The location of the question whose prompt is being shown or hidden.

``rubric_select`` 
----------------------

**Component**: Combined Open-Ended

**Event Source**: Browser

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``location``
     - string
     - The location of the question whose rubric is being selected. 
   * - ``selection``
     - integer
     - Value selected on rubric. 
   * - ``category``
     - integer
     - Rubric category selected.

``oe_show_full_feedback`` and ``oe_show_respond_to_feedback``
------------------------------------------------------------------

**Component**: Combined Open-Ended

**Event Source**: Browser

``event`` **Member Fields**: None.

``oe_feedback_response_selected`` 
--------------------------------------------

**Component**: Combined Open-Ended

**Event Source**: Browser

``event`` **Member Fields**:

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``value``
     - integer
     - Value selected in the feedback response form.

``peer_grading_hide_question`` and ``peer_grading_show_question``
---------------------------------------------------------------------

.. I couldn't find these names in any js file. peer_grading_problem.js includes oe_hide or show_question.

The browser emits ``peer_grading_hide_question`` and
``peer_grading_show_question`` events when the user hides or redisplays a
problem that is peer graded.

**History**: These events were previously named ``peer_grading_hide_problem``
and ``peer_grading_show_problem``.

**Component**: Peer Grading

**Event Source**: Browser

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``location``
     - string
     - The location of the question whose prompt is being shown or hidden.

``staff_grading_hide_question`` and ``staff_grading_show_question``
-----------------------------------------------------------------------

.. staff_grading.js

The browser emits ``staff_grading_hide_question`` and
``staff_grading_show_question`` events when the user hides or redisplays a
problem that is staff graded.

**History**: These events were previously named ``staff_grading_hide_problem``
and ``staff_grading_show_problem``.

**Component**: Staff Grading

**Event Source**: Browser

``event`` **Member Fields**: 

.. list-table::
   :widths: 15 15 60
   :header-rows: 1

   * - Field
     - Type
     - Details
   * - ``location``
     - string
     - The location of the question whose prompt is being shown or hidden.

.. _Instructor_Event_Types:

*************************
Instructor Events
*************************

This section lists the events that the server emits as a result of course team
interaction with the Instructor Dashboard in the LMS.

The schema definitions of each of these events include only the JSON fields
that are common to all events. See :ref:`common`.

* ``dump-answer-dist-csv``
* ``dump-graded-assignments-config``
* ``dump-grades``
* ``dump-grades-csv``
* ``dump-grades-csv-raw``
* ``dump-grades-raw``
* ``list-beta-testers``
* ``list-instructors``
* ``list-staff``
* ``list-students``

.. _rescore_all:

======================================================
``rescore-all-submissions`` and ``reset-all-attempts``
======================================================

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``problem`` 
     - string
   * - ``course``
     - string

.. _rescore_student:

===================================================================
 ``delete-student-module-state`` and ``rescore-student-submission``
===================================================================

.. previously a comma-separated list; "Rows identical after the second column" (which means the name and description columns) were combined

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``problem``
     - string
   * - ``student``
     - string
   * - ``course``
     - string

.. _reset_attempts:

======================================================
``reset-student-attempts``
======================================================

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``old_attempts``
     - string
   * - ``student``
     - string
   * - ``problem``
     - string 
   * - ``course``
     - string

.. _progress:

======================================================
``get-student-progress-page`` 
======================================================

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``student``
     - string
   * - ``instructor``
     - string
   * - ``course``
     - string

======================================================
``add_instructor`` and ``remove_instructor`` 
======================================================

.. previously a comma-separated list; "Rows identical after the second column" (which means the name and description columns) were combined

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``instructor``
     - string

.. _list_forum:

======================================================
List Discussion Staff Events
======================================================

.. previously a comma-separated list; "Rows identical after the second column" (which means the name and description columns) were combined

* ``list-forum-admins``

* ``list-forum-mods``

* ``list-forum-community-TAs``

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``course``
     - string

.. _forum:

======================================================
Manage Discussion Staff Events   
======================================================

.. previously a comma-separated list; "Rows identical after the second column" (which means the name and description columns) were combined

* ``add-forum-admin``

* ``remove-forum-admin``

* ``add-forum-mod``

* ``remove-forum-mod``

* ``add-forum-community-TA``

* ``remove-forum-community-TA``

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``username``
     - string
   * - ``course``
     - string

.. _histogram:

======================================================
``psychometrics-histogram-generation``
======================================================

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``problem``
     - string

.. _user_group:

======================================================
``add-or-remove-user-group``   
======================================================

**Component**: Instructor Dashboard

**Event Source**: Server

``event`` **Fields**: 

.. list-table::
   :widths: 40 40
   :header-rows: 1

   * - Field
     - Type
   * - ``event_name``
     - string
   * - ``user``
     - string
   * - ``event``
     - string

.. _instructor_enrollment:

=============================
Instructor Enrollment Events
=============================

In addition to the enrollment events that are generated when students 
enroll in or unenroll from a course, actions by instructors and course staff
members also generate enrollment events.

* When a course author creates a course, his or her user account is enrolled in
  the course and the server emits an ``edx.course.enrollment.activated`` event.

* When a user with the Instructor or Course Staff role enrolls in a course, the
  server emits ``edx.course.enrollment.activated``. The server emits
  ``edx.course.enrollment.deactivated`` events when these users unenroll from a
  course.

* When a user with the Instructor or Course Staff role uses the **Batch
  Enrollment** feature to enroll students or other staff members in a course,
  the server emits an ``edx.course.enrollment.activated`` event for each
  enrollment. When this feature is used to unenroll students from a course, the
  server emits a ``edx.course.enrollment.deactivated`` for each unenrollment.

For details about the enrollment events, see :ref:`enrollment`.


.. _Creating a Peer Assessment: http://edx.readthedocs.org/projects/edx-open-response-assessments/en/latest/
