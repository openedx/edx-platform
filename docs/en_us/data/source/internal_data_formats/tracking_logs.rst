.. _Tracking Logs:

######################
Tracking Logs
######################

The following is an inventory of all LMS event types.

This inventory is comprised of a table of Common Fields that appear in all events, a table of Student Event Types which lists all interaction with the LMS outside of the Instructor Dashboard, and a table of Instructor Event Types of all interactions with the Instructor Dashboard in the LMS.

In the data package, events are delivered in a log file. 

.. _common:

********************
Common Fields
********************

This section contains a table of the JSON fields that are common to the schema definitions of all events.

+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| Common Field              | Details                                                     | Type        | Values/Format                      |
+===========================+=============================================================+=============+====================================+
| ``agent``                 | Browser agent string of the user who triggered the event.   | string      |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event``                 | Specifics of the triggered event.                           | string/JSON |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event_source``          | Specifies whether the triggered event originated in the     | string      | 'browser', 'server', 'task'        |
|                           | browser or on the server.                                   |             |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event_type``            | The type of event triggered. Values depend on               | string      | See the individual descriptions    |
|                           | ``event_source``                                            |             | that follow.                       |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``ip``                    | IP address of the user who triggered the event.             | string      |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``page``                  | Page user was visiting when the event was fired.            | string      | '$URL'                             |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``session``               | This key identifies the user's session. May be undefined.   | string      | 32 digits                          |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``time``                  | Gives the UTC time at which the event was fired.            | string      | 'YYYY-MM-DDThh:mm:ss.xxxxxx'       |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``username``              | The username of the user who caused the event to fire. This | string      |                                    |
|                           | string is empty for anonymous events (i.e., user not logged |             |                                    |
|                           | in).                                                        |             |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+


****************************************
Student Event Types
****************************************

The Student Event Type table lists the event types that are logged for interactions with the LMS outside the Instructor Dashboard.

* :ref:`navigational`

* :ref:`video`

* :ref:`pdf`

* :ref:`problem`

* :ref:`ora`

A description follows for each event type that includes what each event type represents, which component it originates from, and what ``event`` fields it contains. The ``event_source`` field from the "Common Fields" table above distinguishes between events that originated in the browser (in javascript) and events that originated on the server (during the processing of a request).

.. _navigational:

==============================
Navigational Event Types   
==============================

These event types are fired when a user selects a navigational control. 

* ``seq_goto`` is fired when a user jumps between units in a sequence. 

* ``seq_next`` is fired when a user navigates to the next unit in a sequence. 

* ``seq_prev`` is fired when a user navigates to the previous unit in a sequence. 

**Component**: Sequence **Question:** what does a "sequence" correspond to in Studio? a subsection?

**Event Source**: Browser

``event`` **Fields**: All of the navigational event types have the same fields.

+--------------------+---------------+---------------------------------------------------------------------+
| Field              | Type          | Details                                                             |
+====================+===============+=====================================================================+
| ``old``            | integer       | For ``seq_goto``, the index of the unit being jumped from.          |
|                    |               | For ``seq_next`` and ``seq_prev``, the index of the unit being      |
|                    |               | navigated away from.                                                |
+--------------------+---------------+---------------------------------------------------------------------+
| ``new``            | integer       | For ``seq_goto``, the index of the unit being jumped to.            |
|                    |               | For ``seq_next`` and ``seq_prev``, the index of the unit being      |
|                    |               | navigated to.                                                       |
+--------------------+---------------+---------------------------------------------------------------------+
| ``id``             | integer       | The edX ID of the sequence.                                         |
+--------------------+---------------+---------------------------------------------------------------------+

---------------
``page_close``
---------------

In addition, the ``page_close`` event type originates from within the Logger itself.  

**Component**: Logger

**Event Source**: Browser

``event`` **Fields**: None

.. _video:

==============================
Video Interaction Event Types   
==============================

These event types can fire when a user works with a video.

**Component**: Video

**Event Source**: Browser

---------------------------------
``pause_video``, ``play_video``
---------------------------------

* The ``play_video`` event type is fired on video play. 

* The ``pause_video`` event type is fired on video pause. 

``event`` **Fields**: These event types have the same ``event`` fields.

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``id``              | string        | EdX ID of the video being watched (for example,                     |
|                     |               | i4x-HarvardX-PH207x-video-Simple_Random_Sample).                    |
+---------------------+---------------+---------------------------------------------------------------------+
| ``code``            | string        | YouTube ID of the video being watched (for                          |
|                     |               | example, FU3fCJNs94Y).                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``currentTime``     | float         | Time the video was played at, in seconds.                           |
+---------------------+---------------+---------------------------------------------------------------------+
| ``speed``           | string        | Video speed in use (i.e., 0.75, 1.0, 1.25, 1.50).                   |
|                     |               |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+

-----------------
``seek_video``
-----------------

The ``seek_video`` event is fired when the user clicks the playback bar or transcript to go to a different point in the video file.

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``old_time``        |               | The time in the video that the user is coming from.                 |
+---------------------+---------------+---------------------------------------------------------------------+
| ``new_time``        |               | The time in the video that the user is going to.                    |
+---------------------+---------------+---------------------------------------------------------------------+
| ``type``            |               | The navigational method used to change position within the video.   |
+---------------------+---------------+---------------------------------------------------------------------+

------------------------
``speed_change_video`` 
------------------------

The ``speed_change_video`` event is fired when a user selects a different playing speed for the video. 

**History**: Prior to 12 Feb 2014, this event fired when the user selected either the same speed or a different speed.  

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``current_time``    |               | The time in the video that the user chose to change the             |
|                     |               | playing speed.                                                      |
+---------------------+---------------+---------------------------------------------------------------------+
| ``old_speed``       |               | The speed at which the video was playing.                           |
+---------------------+---------------+---------------------------------------------------------------------+
| ``new_speed``       |               | The speed that the user selected for the video to play.             |
+---------------------+---------------+---------------------------------------------------------------------+

.. types needed

... additional missing video event types TBD

.. _pdf:

==============================
PDF Interaction Event Types   
==============================

The ``book``  event type is fired when a user is reading a PDF book.  

**Component**: PDF Viewer 

**Event Source**: Browser

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``type``            | string        | 'gotopage', 'prevpage', 'nextpage'                                  |
+---------------------+---------------+---------------------------------------------------------------------+
| ``old``             | integer       | Original page number.                                               |
+---------------------+---------------+---------------------------------------------------------------------+
| ``new``             | integer       | Destination page number.                                            |
+---------------------+---------------+---------------------------------------------------------------------+

.. _problem:

=================================
Problem Interaction Event Types 
=================================

----------------------------
``problem_check`` (Browser)
----------------------------

``problem_check`` events are produced by both browser interactions and server requests. A browser fires ``problem_check`` events when a user wants to check a problem.  

**Component**: Capa Module

**Event Source**: Browser

``event`` **Fields**: The ``event`` field contains the values of all input fields from the problem being checked, styled as GET parameters.

-----------------------------
``problem_check``  (Server)
-----------------------------

The server fires ``problem_check`` events when a problem is successfully checked.  

**History**: Originally named ``save_problem_check``.

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``answers``         | dict          |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``attempts``        | integer       |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``correct_map``     | string / JSON | For each problem id value listed by ``answers``, provides:          |
|                     |               +-----------------+----------+----------------------------------------+ 
|                     |               | ``correctness`` | string   | 'correct', 'incorrect'                 |
|                     |               +-----------------+----------+----------------------------------------+ 
|                     |               | ``hint``        | string   | Gives optional hint. Nulls allowed.    |
|                     |               +-----------------+----------+----------------------------------------+ 
|                     |               | ``hintmode``    | string   | None, 'on_request', 'always'. Nulls    |
|                     |               |                 |          | allowed.                               |
|                     |               +-----------------+----------+----------------------------------------+ 
|                     |               | ``msg``         | string   | Gives extra message response.          | 
|                     |               +-----------------+----------+----------------------------------------+ 
|                     |               | ``npoints``     | integer  | Points awarded for this                | 
|                     |               |                 |          | ``answer_id``. Nulls allowed.          |
|                     |               +-----------------+----------+----------------------------------------+
|                     |               | ``queuestate``  | dict     | None when not queued, else             |
|                     |               |                 |          | ``{key:'', time:''}`` where ``key``    |
|                     |               |                 |          | is a secret string dump of a DateTime  |
|                     |               |                 |          | object in the form '%Y%m%d%H%M%S'.     |
|                     |               |                 |          | Nulls allowed.                         |
|                     |               +-----------------+----------+----------------------------------------+
|                     |               |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``grade``           | integer       | Current grade value.                                                |
+---------------------+---------------+---------------------------------------------------------------------+
| ``max_grade``       | integer       | Maximum possible grade value.                                       |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being checked.                                    |
+---------------------+---------------+---------------------------------------------------------------------+
| ``state``           | string / JSON | Current problem state.                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``success``         | string        | 'correct', 'incorrect'                                              |
+---------------------+---------------+---------------------------------------------------------------------+

-----------------------------
``problem_check_fail``
-----------------------------

The server fires ``problem_check_fail`` events when a problem cannot be checked successfully.

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``problem_id``      | string        | ID of the problem being checked.                                    |
+---------------------+---------------+---------------------------------------------------------------------+
| ``answers``         | dict          |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``failure``         | string        | `'closed'`, `'unreset'`                                             |
+---------------------+---------------+---------------------------------------------------------------------+

-----------------------------
``problem_reset``
-----------------------------

``problem_reset`` events fire when a user resets a problem.

**Component**: Capa Module

**Event Source**: Browser

``event`` **Fields**: None

-----------------------------
``problem_rescore``
-----------------------------

The server fires ``problem_rescore`` events when a problem is successfully rescored.  

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``state``           | string / JSON | Current problem state.                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being checked.                                    |
+---------------------+---------------+---------------------------------------------------------------------+
| ``orig_score``      | integer       |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``orig_total``      | integer       |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``new_score``       | integer       |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``new_total``       | integer       |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``correct_map``     | string / JSON | See the fields for the ``problem_check`` server event type above.   |
+---------------------+---------------+---------------------------------------------------------------------+
| ``success``         | string        | 'correct', 'incorrect'                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``attempts``        | integer       |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+

-----------------------------
``problem_rescore_fail``
-----------------------------

The server fires ``problem_rescore_fail`` events when a problem cannot be successfully rescored.  

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``state``           | string / JSON | Current problem state.                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being checked.                                    |
+---------------------+---------------+---------------------------------------------------------------------+
| ``failure``         | string        | 'unsupported', 'unanswered', 'input_error', 'unexpected'            |
+---------------------+---------------+---------------------------------------------------------------------+

-----------------------------
``problem_save``
-----------------------------

``problem_show`` fires when a problem is saved.

**Component**: Capa Module

**Event Source**: Browser

``event`` **Fields**: None

-----------------------------
``problem_show``
-----------------------------

``problem_show`` fires when a problem is shown.  

**Component**: Capa Module

**Event Source**: Browser

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``problem``         | string        | ID of the problem being shown. For example,                         |
|                     |               | i4x://MITx/6.00x/problem/L15:L15_Problem_2).                        |
+---------------------+---------------+---------------------------------------------------------------------+

------------------------------------------------
``reset_problem``
------------------------------------------------

``reset_problem`` fires when a problem has been reset successfully. 

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``old_state``       | string / JSON | Current problem state. **Question** is this really current?         |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being reset.                                      |
+---------------------+---------------+---------------------------------------------------------------------+
| ``new_state``       | string / JSON | New problem state.                                                  |
+---------------------+---------------+---------------------------------------------------------------------+

------------------------------------------------
``reset_problem_fail`` 
------------------------------------------------

``reset_problem_fail`` fires when a problem cannot be reset successfully. 

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``old_state``       | string / JSON | Current problem state. **Question** is this really current?         |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being reset.                                      |
+---------------------+---------------+---------------------------------------------------------------------+
| ``failure``         | string        | 'closed', 'not_done'                                                |
+---------------------+---------------+---------------------------------------------------------------------+

------------------------------------------------
``show_answer`` or ``showanswer`` 
------------------------------------------------

Server-side event which displays the answer to a problem. 

**History**: The original name for this event type was ``showanswer``. **Question** is that correct?

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``problem_id``      | string        | EdX ID of the problem being shown.                                  |
+---------------------+---------------+---------------------------------------------------------------------+

------------------------------------------------
``save_problem_fail`` 
------------------------------------------------

``save_problem_fail``  fires when a problem cannot be saved successfully. 

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``state``           | string / JSON | Current problem state.                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being saved.                                      |
+---------------------+---------------+---------------------------------------------------------------------+
| ``failure``         | string        | 'closed', 'done'                                                    |
+---------------------+---------------+---------------------------------------------------------------------+
| ``answers``         | dict          |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+

------------------------------------------------
``save_problem_success`` 
------------------------------------------------

``save_problem_success`` fires when a problem is saved successfully. 

**Component**: Capa Module

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
|  Field              | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``state``           | string / JSON | Current problem state.                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being saved.                                      |
+---------------------+---------------+---------------------------------------------------------------------+
| ``answers``         | dict          |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+

.. _ora:

======================================
Open Response Assessment Event Types 
======================================

---------------------------------------------------------------------------
``oe_hide_question`` and ``oe_show_question``
---------------------------------------------------------------------------

The ``oe_hide_question`` and ``oe_show_question`` event types fire when the user hides or redisplays a combined open-ended problem.

**History**: These event types were previously named ``oe_hide_problem`` and ``oe_show_problem``.

**Component**: Combined Open-Ended

**Event Source**: Browser

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``location``        | string        | The location of the question whose prompt is being shown or hidden. |
+---------------------+---------------+---------------------------------------------------------------------+

----------------------
``rubric_select`` 
----------------------

**Component**: Combined Open-Ended

**Event Source**: Browser

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``location``        | string        | The location of the question whose rubric is                        |
|                     |               | being selected.                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``selection``       | integer       | Value selected on rubric.                                           |
+---------------------+---------------+---------------------------------------------------------------------+
| ``category``        | integer       | Rubric category selected.                                           |
+-----------------------------------+-------------------------------+---------------------+-----------------+

------------------------------------------------------------------
``oe_show_full_feedback`` and ``oe_show_respond_to_feedback``
------------------------------------------------------------------

**Component**: Combined Open-Ended

**Event Source**: Browser

``event`` **Fields**: None.

--------------------------------------------
``oe_feedback_response_selected`` 
--------------------------------------------

**Component**: Combined Open-Ended

**Event Source**: Browser

``event`` **Fields**:

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``value``           | integer       | Value selected in the feedback response form.                       |
+---------------------+---------------+---------------------------------------------------------------------+

---------------------------------------------------------------------
``peer_grading_hide_question`` and ``peer_grading_show_question``
---------------------------------------------------------------------

The ``peer_grading_hide_question`` and ``peer_grading_show_question`` event types fire when the user hides or redisplays a problem that is peer graded.

**History**: These event types were previously named ``peer_grading_hide_problem`` and ``peer_grading_show_problem``.

**Component**: Peer Grading

**Event Source**: Browser

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``location``        | string        | The location of the question whose prompt is being shown or hidden. |
+---------------------+---------------+---------------------------------------------------------------------+

-----------------------------------------------------------------------
``staff_grading_hide_question`` and ``staff_grading_show_question``
-----------------------------------------------------------------------

The ``staff_grading_hide_question`` and ``staff_grading_show_question`` event types fire when the user hides or redisplays a problem that is staff graded.

**History**: These event types were previously named ``staff_grading_hide_problem`` and ``staff_grading_show_problem``.

**Component**: Staff Grading

**Event Source**: Browser

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``location``        | string        | The location of the question whose prompt is being shown or hidden. |
+---------------------+---------------+---------------------------------------------------------------------+


*************************
Instructor Event Types
*************************

The Instructor Event Type table lists the event types logged for course team interaction with the Instructor Dashboard in the LMS.

.. need a description for each of these

+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| Event Type                             | Component            | Event Source    | ``event`` Fields    | Type          |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``list-students``,                     | Instructor Dashboard | Server          |                     |               |
| ``dump-grades``,                       |                      |                 |                     |               |
| ``dump-grades-raw``,                   |                      |                 |                     |               |
| ``dump-grades-csv``,                   |                      |                 |                     |               |
| ``dump-grades-csv-raw``,               |                      |                 |                     |               |
| ``dump-answer-dist-csv``,              |                      |                 |                     |               |
| ``dump-graded-assignments-config``     |                      |                 |                     |               |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``rescore-all-submissions``,           | Instructor Dashboard | Server          | ``problem``         | string        |
| ``reset-all-attempts``                 |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``course``          | string        |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``delete-student-module-state``,       | Instructor Dashboard | Server          | ``problem``         | string        |
| ``rescore-student-submission``         |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``student``         | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``course``          | string        |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``reset-student-attempts``             | Instructor Dashboard | Server          | ``old_attempts``    | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``student``         | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``problem``         | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``instructor``      | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``course``          | string        |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``get-student-progress-page``          | Instructor Dashboard | Server          | ``student``         | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``instructor``      | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``course``          | string        |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``list-staff``,                        | Instructor Dashboard | Server          |                     |               |
| ``list-instructors``,                  |                      |                 |                     |               |
| ``list-beta-testers``                  |                      |                 |                     |               |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``add-instructor``,                    | Instructor Dashboard | Server          | ``instructor``      | string        |
| ``remove-instructor``                  |                      |                 |                     |               |
|                                        |                      |                 |                     |               |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``list-forum-admins``,                 | Instructor Dashboard | Server          | ``course``          | string        |
| ``list-forum-mods``,                   |                      |                 |                     |               |
| ``list-forum-community-TAs``           |                      |                 |                     |               |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``remove-forum-admin``,                | Instructor Dashboard | Server          | ``username``        | string        |
| ``add-forum-admin``,                   |                      |                 |                     |               |
| ``remove-forum-mod``,                  |                      |                 |                     |               |
| ``add-forum-mod``,                     |                      |                 +---------------------+---------------+
| ``remove-forum-community-TA``,         |                      |                 | ``course``          | string        |
| ``add-forum-community-TA``             |                      |                 |                     |               |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``psychometrics-histogram-generation`` | Instructor Dashboard | Server          | ``problem``         | string        |
|                                        |                      |                 |                     |               |
|                                        |                      |                 |                     |               |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
| ``add-or-remove-user-group``           | Instructor Dashboard | Server          | ``event_name``      | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``user``            | string        |
|                                        |                      |                 +---------------------+---------------+
|                                        |                      |                 | ``event``           | string        |
+----------------------------------------+----------------------+-----------------+---------------------+---------------+
