===============
 Tracking Logs
===============

The following is an inventory of all LMS event types.

This inventory is comprised of a table of Common Fields that appear in all events, a table of Student Event Types which lists all interaction with the LMS outside of the Instructor Dashboard,
and a table of Instructor Event Types of all interaction with the Instructor Dashboard in the LMS.

Common Fields
=============

This section contains a table of fields common to all events.


+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| Common Field              | Details                                                     | Type        | Values/Format                      |
+===========================+=============================================================+=============+====================================+
| ``agent``                 | Browser agent string of the user who triggered the event.   | string      |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event``                 | Specifics of the triggered event.                           | string/JSON |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event_source``          | Specifies whether the triggered event originated in the     | string      | `'browser'`, `'server'`, `'task'`  |
|                           | browser or on the server.                                   |             |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event_type``            | The type of event triggered. Values depend on               | string      | (see below)                        |
|                           | ``event_source``                                            |             |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``ip``                    | IP address of the user who triggered the event.             | string      |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``page``                  | Page user was visiting when the event was fired.            | string      | `'$URL'`                           |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``session``               | This key identifies the user's session. May be undefined.   | string      | 32 digits                          |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``time``                  | Gives the GMT time at which the event was fired.            | string      | `'YYYY-MM-DDThh:mm:ss.xxxxxx'`     |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``username``              | The username of the user who caused the event to fire. This | string      |                                    |
|                           | string is empty for anonymous events (i.e., user not logged |             |                                    |
|                           | in).                                                        |             |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+


Event Types
===========

There are two tables of event types -- one for student events, and one for instructor events.
Table columns describe what each event type represents, which component it originates from, what scripting language was used to fire the event, and what ``event`` fields are associated with it.
The ``event_source`` field from the "Common Fields" table above distinguishes between events that originated in the browser (in javascript) and events that originated on the server (during the processing of a request).

Event types with several different historical names are enumerated by forward slashes.
Rows identical after the second column have been combined, with the corresponding event types enumerated by commas.



Student Event Types
-------------------

The Student Event Type table lists the event types logged for interaction with the LMS outside the Instructor Dashboard.


+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| Event Type                        | Description                   | Component           | Event Source    | ``event`` Fields    | Type          | Details                                                             |
+===================================+===============================+=====================+=================+=====================+===============+=====================================================================+
| ``seq_goto``                      | Fired when a user jumps       | Sequence            | Browser         | ``old``             | integer       | Index of the unit being jumped from.                                |
|                                   | between units in              |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   | a sequence.                   |                     |                 | ``new``             | integer       | Index of the unit being jumped to.                                  |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``id``              | integer       | edX ID of the sequence.                                             |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``seq_next``                      | Fired when a user navigates   | Sequence            | Browser         | ``old``             | integer       | Index of the unit being navigated                                   |
|                                   | to the next unit in a         |                     |                 |                     |               | away from.                                                          |
|                                   | sequence.                     |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``new``             | integer       | Index of the unit being navigated to.                               |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``id``              | integer       | edX ID of the sequence.                                             |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``seq_prev``                      | Fired when a user navigates   | Sequence            | Browser         | ``old``             | integer       | Index of the unit being navigated away                              |
|                                   | to the previous unit in a     |                     |                 |                     |               | from.                                                               |
|                                   | sequence.                     |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``new``             | integer       | Index of the unit being navigated to.                               |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``id``              | integer       | edX ID of the sequence.                                             |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``oe_hide_question`` /            |                               | Combined Open-Ended | Browser         | ``location``        | string        | The location of the question whose prompt is                        |
| ``oe_hide_problem``               |                               |                     |                 |                     |               | being hidden.                                                       |
| ``peer_grading_hide_question`` /  |                               | Peer Grading        |                 |                     |               |                                                                     |
| ``peer_grading_hide_problem``     |                               |                     |                 |                     |               |                                                                     |
| ``staff_grading_hide_question`` / |                               | Staff Grading       |                 |                     |               |                                                                     |
| ``staff_grading_hide_problem``    |                               |                     |                 |                     |               |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``oe_show_question`` /            |                               | Combined Open-Ended | Browser         | ``location``        | string        | The location of the question whose prompt is                        |
| ``oe_show_problem``               |                               |                     |                 |                     |               | being shown.                                                        |
| ``peer_grading_show_question`` /  |                               | Peer Grading        |                 |                     |               |                                                                     |
| ``peer_grading_show_problem``     |                               |                     |                 |                     |               |                                                                     |
| ``staff_grading_show_question`` / |                               | Staff Grading       |                 |                     |               |                                                                     |
| ``staff_grading_show_problem``    |                               |                     |                 |                     |               |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``rubric_select``                 |                               | Combined Open-Ended | Browser         | ``location``        | string        | The location of the question whose rubric is                        |
|                                   |                               |                     |                 |                     |               | being selected.                                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``selection``       | integer       | Value selected on rubric.                                           |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``category``        | integer       | Rubric category selected.                                           |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``oe_show_full_feedback``         |                               | Combined Open-Ended | Browser         |                     |               |                                                                     |
| ``oe_show_respond_to_feedback``   |                               |                     |                 |                     |               |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``oe_feedback_response_selected`` |                               | Combined Open-Ended | Browser         | ``value``           | integer       | Value selected in the feedback response form.                       |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``page_close``                    | This event type originates    | Logger              | Browser         |                     |               |                                                                     |
|                                   | from within the Logger        |                     |                 |                     |               |                                                                     |
|                                   | itself.                       |                     |                 |                     |               |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``play_video``                    | Fired on video play.          | Video               | Browser         | ``id``              | string        | EdX ID of the video being watched (e.g.,                            |
|                                   |                               |                     |                 |                     |               | i4x-HarvardX-PH207x-video-Simple_Random_Sample).                    |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``code``            | string        | YouTube ID of the video being watched (e.g.,                        |
+-----------------------------------+-------------------------------+                     |                 |                     |               | FU3fCJNs94Y).                                                       |
| ``pause_video``                   | Fired on video pause.         |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``currentTime``     | float         | Time the video was played at, in seconds.                           |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``speed``           | string        | Video speed in use (i.e., 0.75, 1.0, 1.25, 1.50).                   |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``seek_video``                    | Fired when a user uses the    | Video               | Browser         | ``old_time``        |               | The time in the video that the user is coming from.                 |
|                                   | scroll bar or the transcript  |                     |                 |                     |               |                                                                     |
|                                   | to go to a different point in |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   | the video file.               |                     |                 | ``new_time``        |               | The time in the video that the user is going to.                    |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``type``            |               | The navigational method used to change position within the video.   |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``speed_change_video``            | Fired when a user selects     | Video               | Browser         | ``current_time``    |               | The time in the video that the user chose to change the             |
|                                   | a different playing speed     |                     |                 |                     |               | playing speed.                                                      |
|                                   | for the video.                |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   | **History**: Prior to 12 Feb  |                     |                 | ``old_speed``       |               | The speed at which the video was playing.                           |
|                                   | 2014, this event fired even   |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   | when the user did not select  |                     |                 | ``new_speed``       |               | The speed that the user selected for the video to play.             |
|                                   | a different speed.            |                     |                 |                     |               |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``book``                          | Fired when a user is reading  | PDF Viewer          | Browser         | ``type``            | string        | `'gotopage'`, `'prevpage'`, `'nextpage'`                            |
|                                   | a PDF book.                   |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``old``             | integer       | Original page number.                                               |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``new``             | integer       | Destination page number.                                            |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_check``                 | Fired when a user wants to    | Capa Module         | Browser         |                     |               | The ``event`` field contains the                                    |
|                                   | check a problem.              |                     |                 |                     |               | values of all input fields from the problem                         |
|                                   |                               |                     |                 |                     |               | being checked, styled as GET parameters.                            |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_check`` /               | Fired when a problem has been | Capa Module         | Server          | ``state``           | string / JSON | Current problem state.                                              |
| ``save_problem_check``            | checked successfully.         |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``problem_id``      | string        | ID of the problem being checked.                                    |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``answers``         | dict          |                                                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``success``         | string        | `'correct'`, `'incorrect'`                                          |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``attempts``        | integer       |                                                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``grade``           | integer       | Current grade value                                                 |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``max_grade``       | integer       | Maximum possible grade value                                        |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``correct_map``     | string / JSON | **See the table in**                                                |
|                                   |                               |                     |                 |                     |               | **Addendum:** ``correct_map`` **Fields and Values below**           |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_check_fail``            | Fired when a problem cannot be| Capa Module         | Server          | ``state``           | string / JSON | Current problem state.                                              |
|                                   | checked successfully.         |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``problem_id``      | string        | ID of the problem being checked.                                    |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``answers``         | dict          |                                                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``failure``         | string        | `'closed'`, `'unreset'`                                             |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_reset``                 | Fired when a user resets a    | Capa Module         | Browser         |                     |               |                                                                     |
|                                   | problem.                      |                     |                 |                     |               |                                                                     |
|                                   |                               |                     |                 |                     |               |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_rescore``               | Fired when a problem is       | Capa Module         | Server          | ``state``           | string / JSON | Current problem state.                                              |
|                                   | rescored sucessfully.         |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``problem_id``      | string        | ID of the problem being rescored.                                   |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``orig_score``      | integer       |                                                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``orig_total``      | integer       |                                                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``new_score``       | integer       |                                                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``new_total``       | integer       |                                                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``correct_map``     | string / JSON | (See above.)                                                        |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``success``         | string        | `'correct'`, `'incorrect'`                                          |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``attempts``        | integer       |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_rescore_fail``          | Fired when a problem cannot be| Capa Module         | Server          | ``state``           | string / JSON | Current problem state.                                              |
|                                   | rescored successfully.        |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``problem_id``      | string        | ID of the problem being rescored.                                   |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``failure``         | string        | `'unsupported'`, `'unanswered'`, `'input_error'`, `'unexpected'`    |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_show``                  | Fired when a problem is       | Capa Module         | Browser         | ``problem``         | string        | ID of the problem being shown (e.g.,                                |
|                                   | shown.                        |                     |                 |                     |               | i4x://MITx/6.00x/problem/L15:L15_Problem_2).                        |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_save``                  | Fired when a problem is       | Capa Module         | Browser         |                     |               |                                                                     |
|                                   | saved.                        |                     |                 |                     |               |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``reset_problem``                 | Fired when a problem has been | Capa Module         | Server          | ``old_state``       | string / JSON | Current problem state.                                              |
|                                   | reset successfully.           |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``problem_id``      | string        | ID of the problem being reset.                                      |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``new_state``       | string / JSON | New problem state.                                                  |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``reset_problem_fail``            | Fired when a problem cannot be| Capa Module         | Server          | ``old_state``       | string / JSON | Current problem state.                                              |
|                                   | reset successfuly.            |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``problem_id``      | string        |  ID of the problem being reset.                                     |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``failure``         | string        | `'closed'`, `'not_done'`                                            |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``showanswer`` /                  | Server-side event which       | Capa Module         | Server          | ``problem_id``      | string        | EdX ID of the problem being shown.                                  |
| ``show_answer``                   | displays the answer to a      |                     |                 |                     |               |                                                                     |
|                                   | problem.                      |                     |                 |                     |               |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``save_problem_fail``             | Fired when a problem cannot be| Capa Module         | Server          | ``state``           | string / JSON | Current problem state.                                              |
|                                   | saved successfully.           |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``problem_id``      | string        | ID of the problem being saved.                                      |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``failure``         | string        | `'closed'`, `'done'`                                                |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``answers``         | dict          |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``save_problem_success``          | Fired when a problem has been | Capa Module         | Server          | ``state``           | string / JSON | Current problem state.                                              |
|                                   | successfully saved.           |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``problem_id``      | string        | ID of the problem being saved.                                      |
|                                   |                               |                     |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                   |                               |                     |                 | ``answers``         | dict          |                                                                     |
+-----------------------------------+-------------------------------+---------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+

*Addendum:* ``correct_map`` *Fields and Values*
-----------------------------------------------

Table of ``correct_map`` field types and values for the ``problem_check`` student event type above.

+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+
| ``correct_map`` **field**                        |  **Type**                                        | **Values / Format**                              |  **Null Allowed?**                               |
+==================================================+==================================================+==================================================+==================================================+
| ``answer_id``                                    | string                                           |                                                  |                                                  |
+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+
| ``correctness``                                  | string                                           | `'correct'`, `'incorrect'`                       |                                                  |
+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+
| ``npoints``                                      | integer                                          | Points awarded for this ``answer_id``.           | yes                                              |
+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+
| ``msg``                                          | string                                           | Gives extra message response.                    |                                                  |
+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+
| ``hint``                                         | string                                           | Gives optional hint.                             | yes                                              |
+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+
| ``hintmode``                                     | string                                           | None, `'on_request'`, `'always'`                 | yes                                              |
+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+
| ``queuestate``                                   | dict                                             | None when not queued, else `{key:' ', time:' '}` | yes                                              |
|                                                  |                                                  | where key is a secret string and time is a       |                                                  |
|                                                  |                                                  | string dump of a DateTime object of the form     |                                                  |
|                                                  |                                                  | `'%Y%m%d%H%M%S'`.                                |                                                  |
+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+--------------------------------------------------+


Instructor Event Types
----------------------


The Instructor Event Type table lists the event types logged for course team interaction with the Instructor Dashboard in the LMS.


+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| Event Type                             | Description                   | Component            | Event Source    | ``event`` Fields    | Type          | Details                                                             |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``list-students``,                     |                               | Instructor Dashboard | Server          |                     |               |                                                                     |
| ``dump-grades``,                       |                               |                      |                 |                     |               |                                                                     |
| ``dump-grades-raw``,                   |                               |                      |                 |                     |               |                                                                     |
| ``dump-grades-csv``,                   |                               |                      |                 |                     |               |                                                                     |
| ``dump-grades-csv-raw``,               |                               |                      |                 |                     |               |                                                                     |
| ``dump-answer-dist-csv``,              |                               |                      |                 |                     |               |                                                                     |
| ``dump-graded-assignments-config``     |                               |                      |                 |                     |               |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``rescore-all-submissions``,           |                               | Instructor Dashboard | Server          | ``problem``         | string        |                                                                     |
| ``reset-all-attempts``                 |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``course``          | string        |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``delete-student-module-state``,       |                               | Instructor Dashboard | Server          | ``problem``         | string        |                                                                     |
| ``rescore-student-submission``         |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``student``         | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``course``          | string        |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``reset-student-attempts``             |                               | Instructor Dashboard | Server          | ``old_attempts``    | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``student``         | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``problem``         | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``instructor``      | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``course``          | string        |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``get-student-progress-page``          |                               | Instructor Dashboard | Server          | ``student``         | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``instructor``      | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``course``          | string        |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``list-staff``,                        |                               | Instructor Dashboard | Server          |                     |               |                                                                     |
| ``list-instructors``,                  |                               |                      |                 |                     |               |                                                                     |
| ``list-beta-testers``                  |                               |                      |                 |                     |               |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``add-instructor``,                    |                               | Instructor Dashboard | Server          | ``instructor``      | string        |                                                                     |
| ``remove-instructor``                  |                               |                      |                 |                     |               |                                                                     |
|                                        |                               |                      |                 |                     |               |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``list-forum-admins``,                 |                               | Instructor Dashboard | Server          | ``course``          | string        |                                                                     |
| ``list-forum-mods``,                   |                               |                      |                 |                     |               |                                                                     |
| ``list-forum-community-TAs``           |                               |                      |                 |                     |               |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``remove-forum-admin``,                |                               | Instructor Dashboard | Server          | ``username``        | string        |                                                                     |
| ``add-forum-admin``,                   |                               |                      |                 |                     |               |                                                                     |
| ``remove-forum-mod``,                  |                               |                      |                 |                     |               |                                                                     |
| ``add-forum-mod``,                     |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
| ``remove-forum-community-TA``,         |                               |                      |                 | ``course``          | string        |                                                                     |
| ``add-forum-community-TA``             |                               |                      |                 |                     |               |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``psychometrics-histogram-generation`` |                               | Instructor Dashboard | Server          | ``problem``         | string        |                                                                     |
|                                        |                               |                      |                 |                     |               |                                                                     |
|                                        |                               |                      |                 |                     |               |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
| ``add-or-remove-user-group``           |                               | Instructor Dashboard | Server          | ``event_name``      | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``user``            | string        |                                                                     |
|                                        |                               |                      |                 +---------------------+---------------+---------------------------------------------------------------------+
|                                        |                               |                      |                 | ``event``           | string        |                                                                     |
+----------------------------------------+-------------------------------+----------------------+-----------------+---------------------+---------------+---------------------------------------------------------------------+
