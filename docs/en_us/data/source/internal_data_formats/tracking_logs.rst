.. _Tracking Logs:

######################
Tracking Logs
######################

This chapter provides reference information about the event data that is delivered in data packages. Events are initiated by interactions with the courseware and the Instructor Dashboard in the LMS, and are stored in JSON documents. In the data package, event data is delivered in a log file. 

The sections in this chapter describe:

* A :ref:`sample_events`.
* :ref:`common` that are included in the JSON document of every event type.
* :ref:`Student_Event_Types` for interactions with the LMS outside of the Instructor Dashboard.
* :ref:`Instructor_Event_Types` for interactions with the Instructor Dashboard in the LMS.

.. _sample_events:

*************************
Sample Event
*************************

A sample event from an edX.log file follows. The JSON documents that include the event data are included in the log file as raw data, so they appear in this compact format.

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

This section contains a table of the JSON fields that are common to the schema definitions of all events.

+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| Field                     | Details                                                     | Type        | Values/Format/Member Fields        |
+===========================+=============================================================+=============+====================================+
| ``agent``                 | Browser agent string of the user who triggered the event.   | string      |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``context``               | For all event types, identifies the course that generated   | string/JSON | Contains these common member       |
|                           | the event, the organization that lists the course, and the  |             | fields:                            |  
|                           | individual who is performing the action.                    |             | ``course_id``                      |
|                           |                                                             |             | ``org_id``                         |
|                           | ``course_user_tags`` contains a dictionary with the key(s)  |             | ``user_id``                        |
|                           |  and value(s) from the ``user_api_usercoursetag`` table     |             | ``course_user_tags``               |    
|                           |  for the user. See :ref:`user_api_usercoursetag`.           |             |                                    | 
|                           |                                                             |             | These fields are blank if values   |
|                           | Also contains member fields that apply to specific event    |             | cannot be determined.              |
|                           | types only: see the description for each event type.        |             |                                    |
|                           |                                                             |             |                                    |
|                           | **History**: Added 23 Oct 2013; ``user_id`` added           |             |                                    |
|                           | 6 Nov 2013. Other event fields may duplicate this data.     |             |                                    |
|                           | ``course_user_tags`` added 12 Mar 2014.                     |             |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event``                 | Specifics of the triggered event.                           | string/JSON |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event_source``          | Specifies whether the triggered event originated in the     | string      | 'browser', 'server', 'task'        |
|                           | browser or on the server.                                   |             |                                    |
+---------------------------+-------------------------------------------------------------+-------------+------------------------------------+
| ``event_type``            | The type of event triggered. Values depend on               | string      | For descriptions of member fields, |
|                           | ``event_source``.                                           |             | see the event type descriptions    |
|                           |                                                             |             | that follow.                       |
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

.. _Student_Event_Types:

****************************************
Student Event Types
****************************************

The Student Event Type table lists the event types that are logged for interactions with the LMS outside the Instructor Dashboard.

* :ref:`navigational`

* :ref:`video`

* :ref:`pdf`

* :ref:`problem`

* :ref:`ora`

* :ref:`AB_Event_Types`

The descriptions that follow include what each event type represents, which component it originates from, and what ``event`` fields it contains. The ``event_source`` field from the "Common Fields" table above distinguishes between events that originate in the browser (in javascript) and events that originate on the server (during the processing of a request).

.. _navigational:

==============================
Navigational Event Types   
==============================

These event types are fired when a user selects a navigational control. 

* ``seq_goto`` fires when a user jumps between units in a sequence. 

* ``seq_next`` fires when a user navigates to the next unit in a sequence. 

* ``seq_prev`` fires when a user navigates to the previous unit in a sequence. 

**Component**: Sequence 

.. **Question:** what does a "sequence" correspond to in Studio? a subsection?

**Event Source**: Browser

``event`` **Fields**: These navigational event types all have the same fields.

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

* The ``pause_video`` event type fires on video pause. 

* The ``play_video`` event type fires on video play. 

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

The ``seek_video`` event fires when the user clicks the playback bar or transcript to go to a different point in the video file.

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

The ``speed_change_video`` event fires when a user selects a different playing speed for the video. 

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

.. additional missing video event types TBD

.. _pdf:

=================================
Textbook Interaction Event Types   
=================================

----------
``book``
----------

The ``book`` event type fires when a user navigates within the PDF Viewer or the
PNG Viewer.

* For textbooks in PDF format, the URL in the common ``page`` field contains
  '/pdfbook/'.
* For textbooks in PNG format, the URL in the common ``page`` field contains
  '/book/'.

**Component**: PDF Viewer, PNG Viewer 

**Event Source**: Browser

**History**: This event type changed on 16 Apr 2014 to include the ``name`` and
``chapter`` fields.

``event`` **Fields**: 

+-------------+---------+----------------------------------------------------------------------------------+
| Field       | Type    | Details                                                                          |
+=============+=========+==================================================================================+
| ``type``    | string  | 'gotopage' fires when a page loads after the student manually enters its number. |
|             |         +----------------------------------------------------------------------------------+
|             |         | 'prevpage' fires when the next page button is clicked.                           |
|             |         +----------------------------------------------------------------------------------+
|             |         | 'nextpage' fires when the previous page button is clicked.                       |
+-------------+---------+----------------------------------------------------------------------------------+
| ``name``    | string  | For 'gotopage', set to ``textbook.pdf.page.loaded``.                             |
|             |         +----------------------------------------------------------------------------------+
|             |         | For 'prevpage', set to ``textbook.pdf.page.navigatedprevious``.                  |
|             |         +----------------------------------------------------------------------------------+
|             |         | For 'nextpage', set to ``textbook.pdf.page.navigatednext``.                      |
|             |         +----------------------------------------------------------------------------------+
|             |         | **History**: Added for events produced by the PDF Viewer on 16 Apr 2014.         |
+-------------+---------+----------------------------------------------------------------------------------+
| ``chapter`` | string  | The name of the PDF file.                                                        |
|             |         +----------------------------------------------------------------------------------+
|             |         | **History**: Added for events produced by the PDF Viewer on 16 Apr 2014.         |
+-------------+---------+----------------------------------------------------------------------------------+
| ``old``     | integer | The original page number. Applies to 'gotopage' event types only.                |
+-------------+---------+----------------------------------------------------------------------------------+
| ``new``     | integer | Destination page number.                                                         |
+-------------+---------+----------------------------------------------------------------------------------+

------------------------------------
``textbook.pdf.thumbnails.toggled``
------------------------------------

The ``textbook.pdf.thumbnails.toggled`` event type fires when a user clicks
on the icon to show or hide page thumbnails.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------+---------+---------------------------------------------------------------------+
| Field       | Type    | Details                                                             |
+=============+=========+=====================================================================+
| ``name``    | string  | ``textbook.pdf.thumbnails.toggled``                                 |
+-------------+---------+---------------------------------------------------------------------+
| ``chapter`` | string  | The name of the PDF file.                                           |
+-------------+---------+---------------------------------------------------------------------+
| ``page``    | integer | The number of the page that is open when the user clicks this icon. |
+-------------+---------+---------------------------------------------------------------------+

------------------------------------
``textbook.pdf.thumbnail.navigated``
------------------------------------

The ``textbook.pdf.thumbnail.navigated`` event type fires when a user clicks
on a thumbnail image to navigate to a page.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+---------------------+---------+-------------------------------------------------+
| Field               | Type    | Details                                         |
+=====================+=========+=================================================+
| ``name``            | string  | ``textbook.pdf.thumbnail.navigated``            |
+---------------------+---------+-------------------------------------------------+
| ``chapter``         | string  | The name of the PDF file.                       |
+---------------------+---------+-------------------------------------------------+
| ``page``            | integer | The page number of the thumbnail clicked.       |
+---------------------+---------+-------------------------------------------------+
| ``thumbnail_title`` | string  | The identifying name for the destination of the |
|                     |         | thumbnail. For example, Page 2.                 |
+---------------------+---------+-------------------------------------------------+

------------------------------------
``textbook.pdf.outline.toggled``
------------------------------------

The ``textbook.pdf.outline.toggled`` event type fires when a user clicks the
outline icon to show or hide a list of the book's chapters. 

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------+---------+---------------------------------------------------------------------+
| Field       | Type    | Details                                                             |
+=============+=========+=====================================================================+
| ``name``    | string  | ``textbook.pdf.outline.toggled``                                    |
+-------------+---------+---------------------------------------------------------------------+
| ``chapter`` | string  | The name of the PDF file.                                           |
+-------------+---------+---------------------------------------------------------------------+
| ``page``    | integer | The number of the page that is open when the user clicks this link. |
+-------------+---------+---------------------------------------------------------------------+

------------------------------------
``textbook.pdf.chapter.navigated``
------------------------------------

The ``textbook.pdf.chapter.navigated`` event type fires when a user clicks on
a link in the outline to navigate to a chapter.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------------+---------+-------------------------------------------------+
| Field             | Type    | Details                                         |
+===================+=========+=================================================+
| ``name``          | string  | ``textbook.pdf.chapter.navigated``              |
+-------------------+---------+-------------------------------------------------+
| ``chapter``       | string  | The name of the PDF file.                       |
+-------------------+---------+-------------------------------------------------+
| ``chapter_title`` | string  | The identifying name for the destination of the |
|                   |         | outline link.                                   |
+-------------------+---------+-------------------------------------------------+

------------------------------------
``textbook.pdf.page.navigated``
------------------------------------

The ``textbook.pdf.page.navigated`` event type fires when a user manually enters
a page number.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------+---------+--------------------------------------------------+
| Field       | Type    | Details                                          |
+=============+=========+==================================================+
| ``name``    | string  | ``textbook.pdf.page.navigated``                  |
+-------------+---------+--------------------------------------------------+
| ``chapter`` | string  | The name of the PDF file.                        |
+-------------+---------+--------------------------------------------------+
| ``page``    | integer | The destination page number entered by the user. |
+-------------+---------+--------------------------------------------------+

--------------------------------------
``textbook.pdf.zoom.buttons.changed``
--------------------------------------

The ``textbook.pdf.zoom.buttons.changed`` event type fires when a user clicks
either the Zoom In or Zoom Out icon.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+---------------+---------+--------------------------------------------------------------------+
| Field         | Type    | Details                                                            |
+===============+=========+====================================================================+
| ``name``      | string  | ``textbook.pdf.zoom.buttons.changed``                              |
+---------------+---------+--------------------------------------------------------------------+
| ``direction`` | string  | 'in', 'out'                                                        |
+---------------+---------+--------------------------------------------------------------------+
| ``chapter``   | string  | The name of the PDF file.                                          |
+---------------+---------+--------------------------------------------------------------------+
| ``page``      | integer | The number of the page that is open when the user clicks the icon. |
+---------------+---------+--------------------------------------------------------------------+

------------------------------------
``textbook.pdf.zoom.menu.changed``
------------------------------------

The ``textbook.pdf.zoom.menu.changed`` event type fires when a user selects a
magnification setting.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------+---------+--------------------------------------------------------------------------------+
| Field       | Type    | Details                                                                        |
+=============+=========+================================================================================+
| ``name``    | string  | ``textbook.pdf.zoom.menu.changed``                                             |
+-------------+---------+--------------------------------------------------------------------------------+
| ``amount``  | string  | '1', '0.75', '1.5', 'custom', 'page_actual', 'auto', 'page_width', 'page_fit'. |
+-------------+---------+--------------------------------------------------------------------------------+
| ``chapter`` | string  | The name of the PDF file.                                                      |
+-------------+---------+--------------------------------------------------------------------------------+
| ``page``    | integer | The number of the page that is open when the user selects this value.          |
+-------------+---------+--------------------------------------------------------------------------------+

------------------------------------
``textbook.pdf.display.scaled``
------------------------------------

The ``textbook.pdf.display.scaled`` event type fires when the display
magnification changes. These changes occur after a student selects a
magnification setting from the zoom menu or resizes the browser window.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------+---------+-------------------------------------------------------------------+
| Field       | Type    | Details                                                           |
+=============+=========+===================================================================+
| ``name``    | string  | ``textbook.pdf.display.scaled``                                   |
+-------------+---------+-------------------------------------------------------------------+
| ``amount``  | string  | The magnification setting; for example, 0.95 or 1.25.             |
+-------------+---------+-------------------------------------------------------------------+
| ``chapter`` | string  | The name of the PDF file.                                         |
+-------------+---------+-------------------------------------------------------------------+
| ``page``    | integer | The number of the page that is open when the scaling takes place. |
+-------------+---------+-------------------------------------------------------------------+

------------------------------------
``textbook.pdf.display.scrolled``
------------------------------------

The ``textbook.pdf.display.scrolled`` event type fires each time the displayed
page changes while a user scrolls up or down.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+---------------+---------+---------------------------------------------------------------------+
| Field         | Type    | Details                                                             |
+===============+=========+=====================================================================+
| ``name``      | string  | ``textbook.pdf.display.scrolled``                                   |
+---------------+---------+---------------------------------------------------------------------+
| ``chapter``   | string  | The name of the PDF file.                                           |
+---------------+---------+---------------------------------------------------------------------+
| ``page``      | integer | The number of the page that is open when the scrolling takes place. |
+---------------+---------+---------------------------------------------------------------------+
| ``direction`` | string  | 'up', 'down'                                                        |
+---------------+---------+---------------------------------------------------------------------+

------------------------------------
``textbook.pdf.search.executed``
------------------------------------

The ``textbook.pdf.search.executed`` event type fires when a user searches for a
text value in the file. To reduce the number of events produced, instead of
producing one event per entered character this event type defines a search
string as the set of characters that are consecutively entered in the search
field within 500ms of each other.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------------+---------+------------------------------------------------------------------+
| Field             | Type    | Details                                                          |
+===================+=========+==================================================================+
| ``name``          | string  | ``textbook.pdf.search.executed``                                 |
+-------------------+---------+------------------------------------------------------------------+
| ``query``         | string  | The value in the search field.                                   |
+-------------------+---------+------------------------------------------------------------------+
| ``caseSensitive`` | boolean | 'true' if the case sensitive option is selected,                 |
|                   |         | 'false' if this option is not selected.                          |
+-------------------+---------+------------------------------------------------------------------+
| ``highlightAll``  | boolean | 'true' if the option to highlight all matches is selected,       |
|                   |         | 'false' if this option is not selected.                          |
+-------------------+---------+------------------------------------------------------------------+
| ``status``        | string  | A "not found" status phrase for a search string that             |
|                   |         | is unsuccessful. Blank for successful search strings.            |
+-------------------+---------+------------------------------------------------------------------+
| ``chapter``       | string  | The name of the PDF file.                                        |
+-------------------+---------+------------------------------------------------------------------+
| ``page``          | integer | The number of the page that is open when the search takes place. |
+-------------------+---------+------------------------------------------------------------------+

---------------------------------------------
``textbook.pdf.search.navigatednext``
---------------------------------------------

The ``textbook.pdf.search.navigatednext`` event type fires when a user clicks
on the Find Next or Find Previous icons for an entered search string.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------------+---------+------------------------------------------------------------------+
| Field             | Type    | Details                                                          |
+===================+=========+==================================================================+
| ``name``          | string  | ``textbook.pdf.search.navigatednext``                            |
+-------------------+---------+------------------------------------------------------------------+
| ``findprevious``  | string  | 'true' if the user clicks the Find Previous icon, 'false'        |
|                   |         | if the user clicks the Find Next icon.                           |
+-------------------+---------+------------------------------------------------------------------+
| ``query``         | string  | The value in the search field.                                   |
+-------------------+---------+------------------------------------------------------------------+
| ``caseSensitive`` | boolean | 'true' if the case sensitive option is selected,                 |
|                   |         | 'false' if this option is not selected.                          |
+-------------------+---------+------------------------------------------------------------------+
| ``highlightAll``  | boolean | 'true' if the option to highlight all matches is selected,       |
|                   |         | 'false' if this option is not selected.                          |
+-------------------+---------+------------------------------------------------------------------+
| ``status``        | string  | A "not found" status phrase for a search string that             |
|                   |         | is unsuccessful. Blank for successful search strings.            |
+-------------------+---------+------------------------------------------------------------------+
| ``chapter``       | string  | The name of the PDF file.                                        |
+-------------------+---------+------------------------------------------------------------------+
| ``page``          | integer | The number of the page that is open when the search takes place. |
+-------------------+---------+------------------------------------------------------------------+

---------------------------------------------
``textbook.pdf.search.highlight.toggled``
---------------------------------------------

The ``textbook.pdf.search.highlight.toggled`` event type fires when a user
selects or clears the **Highlight All** option for a search.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------------+---------+------------------------------------------------------------------+
| Field             | Type    | Details                                                          |
+===================+=========+==================================================================+
| ``name``          | string  | ``textbook.pdf.search.highlight.toggled``                        |
+-------------------+---------+------------------------------------------------------------------+
| ``query``         | string  | The value in the search field.                                   |
+-------------------+---------+------------------------------------------------------------------+
| ``caseSensitive`` | boolean | 'true' if the case sensitive option is selected,                 |
|                   |         | 'false' if this option is not selected.                          |
+-------------------+---------+------------------------------------------------------------------+
| ``highlightAll``  | boolean | 'true' if the option to highlight all matches is selected,       |
|                   |         | 'false' if this option is not selected.                          |
+-------------------+---------+------------------------------------------------------------------+
| ``status``        | string  | A "not found" status phrase for a search string that is          |
|                   |         | unsuccessful. Blank for successful search strings.               |
+-------------------+---------+------------------------------------------------------------------+
| ``chapter``       | string  | The name of the PDF file.                                        |
+-------------------+---------+------------------------------------------------------------------+
| ``page``          | integer | The number of the page that is open when the search takes place. |
+-------------------+---------+------------------------------------------------------------------+

------------------------------------------------------
``textbook.pdf.search.casesensitivity.toggled``
------------------------------------------------------

The ``textbook.pdf.search.casesensitivity.toggled`` event type fires when a
user selects or clears the **Match Case** option for a search.

**Component**: PDF Viewer 

**Event Source**: Browser

**History**: This event type was added on 16 Apr 2014.

``event`` **Fields**: 

+-------------------+---------+------------------------------------------------------------------+
| Field             | Type    | Details                                                          |
+===================+=========+==================================================================+
| ``name``          | string  | ``textbook.pdf.search.casesensitivity.toggled``                  |
+-------------------+---------+------------------------------------------------------------------+
| ``query``         | string  | The value in the search field.                                   |
+-------------------+---------+------------------------------------------------------------------+
| ``caseSensitive`` | boolean | 'true' if the case sensitive option is selected,                 |
|                   |         | 'false' if this option is not selected.                          |
+-------------------+---------+------------------------------------------------------------------+
| ``highlightAll``  | boolean | 'true' if the option to highlight all matches is selected,       |
|                   |         | 'false' if this option is not selected.                          |
+-------------------+---------+------------------------------------------------------------------+
| ``status``        | string  | A "not found" status phrase for a search string that             |
|                   |         | is unsuccessful. Blank for successful search strings.            |
+-------------------+---------+------------------------------------------------------------------+
| ``chapter``       | string  | The name of the PDF file.                                        |
+-------------------+---------+------------------------------------------------------------------+
| ``page``          | integer | The number of the page that is open when the search takes place. |
+-------------------+---------+------------------------------------------------------------------+

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
``problem_check`` (Server)
-----------------------------

The server fires ``problem_check`` events when a problem is successfully checked.  

**Component**: Capa Module

**Event Source**: Server

**History**: 

* On 5 Mar 2014, the ``submission`` dictionary was added to the ``event`` field and  ``module`` was added to the ``context`` field.

* Prior to 15 Oct 2013, this event type was named ``save_problem_check``.

* Prior to 15 Jul 2013, this event was fired twice for the same action.

``context`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details and Member Fields                                           |
+=====================+===============+=====================================================================+
| ``module``          | dict          | Provides the specific problem component as part of the context.     |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``display_name``  | string  | The **Display Name** given to the     |
|                     |               |                   |         | problem component.                    |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               |                                                                     | 
+---------------------+---------------+---------------------------------------------------------------------+

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details and Member Fields                                           |
+=====================+===============+=====================================================================+
| ``answers``         | dict          | The problem ID and the internal answer identifier in a name:value   |
|                     |               | pair. For a component with multiple problems, every problem and     |
|                     |               | answer are listed.                                                  |
+---------------------+---------------+---------------------------------------------------------------------+
| ``attempts``        | integer       | The number of times the user attempted to answer the problem.       |
+---------------------+---------------+---------------------------------------------------------------------+
| ``correct_map``     | string / JSON | For each problem ID value listed by ``answers``, provides:          |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``correctness``   | string  | 'correct', 'incorrect'                |
|                     |               +-------------------+---------+---------------------------------------+  
|                     |               | ``hint``          | string  | Gives optional hint. Nulls allowed.   |
|                     |               +-------------------+---------+---------------------------------------+  
|                     |               | ``hintmode``      | string  | None, 'on_request', 'always'. Nulls   |
|                     |               |                   |         | allowed.                              |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``msg``           | string  | Gives extra message response.         | 
|                     |               +-------------------+---------+---------------------------------------+  
|                     |               | ``npoints``       | integer | Points awarded for this               | 
|                     |               |                   |         | ``answer_id``. Nulls allowed.         |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``queuestate``    | dict    | None when not queued, else            |
|                     |               |                   |         | ``{key:'', time:''}`` where ``key``   |
|                     |               |                   |         | is a secret string dump of a DateTime |
|                     |               |                   |         | object in the form '%Y%m%d%H%M%S'.    |
|                     |               |                   |         | Nulls allowed.                        |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``grade``           | integer       | Current grade value.                                                |
+---------------------+---------------+---------------------------------------------------------------------+
| ``max_grade``       | integer       | Maximum possible grade value.                                       |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem that was checked.                                 |
+---------------------+---------------+---------------------------------------------------------------------+
| ``state``           | string / JSON | Current problem state.                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``submission``      | object        | Provides data about the response made. For components that include  |
|                     |               | multiple problems, separate submission objects are provided for     |
|                     |               | each one.                                                           |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``answer``        | string  | The value that the student entered,   |
|                     |               |                   |         | or the display name of the value      |
|                     |               |                   |         | selected.                             |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``correct``       | Boolean | 'true', 'false'                       |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``input_type``    | string  | The type of value that the student    |
|                     |               |                   |         | supplies for the ``response_type``.   | 
|                     |               |                   |         | Based on the XML element names used   | 
|                     |               |                   |         | in the Advanced Editor. Examples      | 
|                     |               |                   |         | include 'checkboxgroup', 'radiogroup',| 
|                     |               |                   |         | 'choicegroup', and 'textline'.        |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``question``      | string  | Provides the text of the question.    |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``response_type`` | string  | The type of problem. Based on the XML | 
|                     |               |                   |         | element names used in the Advanced    | 
|                     |               |                   |         | Editor. Examples include              |
|                     |               |                   |         | 'choiceresponse', 'optionresponse',   |
|                     |               |                   |         | and 'multiplechoiceresponse'.         |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               | ``variant``       | integer | For problems that use problem         |
|                     |               |                   |         | randomization features such as answer |
|                     |               |                   |         | pools or choice shuffling, contains   |
|                     |               |                   |         | the unique ID of the variant that was |
|                     |               |                   |         | presented to this user.               |
|                     |               +-------------------+---------+---------------------------------------+ 
|                     |               |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``success``         | string        | 'correct', 'incorrect'                                              |
+---------------------+---------------+---------------------------------------------------------------------+

-----------------------------
``problem_check_fail``
-----------------------------

The server fires ``problem_check_fail`` events when a problem cannot be checked successfully.

**Component**: Capa Module

**Event Source**: Server

**History**: Prior to 15 Oct 2013, this event type was named ``save_problem_check_fail``.

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``state``           | string / JSON | Current problem state.                                              |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being checked.                                    |
+---------------------+---------------+---------------------------------------------------------------------+
| ``answers``         | dict          |                                                                     |
+---------------------+---------------+---------------------------------------------------------------------+
| ``failure``         | string        | 'closed', 'unreset'                                                 |
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
| ``problem_id``      | string        | ID of the problem being rescored.                                   |
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

``problem_save`` fires when a problem is saved.

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
| ``old_state``       | string / JSON | The state of the problem before the reset was performed.            |
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
| ``old_state``       | string / JSON | The state of the problem before the reset was requested.            |
+---------------------+---------------+---------------------------------------------------------------------+
| ``problem_id``      | string        | ID of the problem being reset.                                      |
+---------------------+---------------+---------------------------------------------------------------------+
| ``failure``         | string        | 'closed', 'not_done'                                                |
+---------------------+---------------+---------------------------------------------------------------------+

------------------------------------------------
``show_answer`` 
------------------------------------------------

Server-side event which displays the answer to a problem. 

**Component**: Capa Module

**Event Source**: Server

**History**: The original name for this event type was ``showanswer``. 

.. **Question** is this renaming info correct?

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

.. _AB_Event_Types:

==========================
A/B Testing Event Types
==========================

Course authors can configure course content to present modules that contain other modules. For example, a parent module can include two child modules with content that differs in some way for comparison testing. When a student navigates to a module that is set up for A/B testing in this way, the student is randomly assigned to a group and shown only one of the child modules. 

* Internally, a *partition* defines the type of experiment: between video and text, for example. A course can include any number of modules with the same partition, or experiment type.
* For each partition, students are randomly assigned to a *group*. The group determines which content, either video or text in this example, is shown by every module with that partitioning. 

The event types that follow apply to modules that are set up to randomly assign students to groups so that different content can be shown to the different groups. 

**History**: These event types were added on 12 Mar 2014.

----------------------------------
``assigned_user_to_partition``
----------------------------------

When a student views a module that is set up to test different child modules, the server checks the ``user_api_usercoursetag`` table for the student's assignment to the relevant partition, and to a group for that partition. The partition ID is the ``user_api_usercoursetag.key`` and the group ID is the ``user_api_usercoursetag.value``. If the student does not yet have an assignment, the server fires an ``assigned_user_to_partition`` event and adds a row to the ``user_api_usercoursetag`` table for the student. See :ref:`user_api_usercoursetag`. 

.. note:: After this event fires, the common ``context`` field in all subsequent events includes a ``course_user_tags`` member field with the student's assigned partition and group.

**Component**: Split Test

**Event Source**: Browser

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``group_id``        | integer       | Identifier of the group.                                            |
+---------------------+---------------+---------------------------------------------------------------------+
| ``group_name``      | string        | Name of the group.                                                  |
+---------------------+---------------+---------------------------------------------------------------------+
| ``partition_id``    | integer       | Identifier for the partition, in the format                         |
|                     |               | ``xblock.partition_service.partition_ID`` where ID is an integer.   |
+---------------------+---------------+---------------------------------------------------------------------+
| ``partition_name``  | string        | Name of the partition.                                              |
+---------------------+---------------+---------------------------------------------------------------------+

----------------------------------
``child_render``
----------------------------------

When a student views a module that is set up to test different content using child modules, a ``child_render`` event fires to identify the child module that is shown to the student. 

**Component**: Split Test

**Event Source**: Server

``event`` **Fields**: 

+---------------------+---------------+---------------------------------------------------------------------+
| Field               | Type          | Details                                                             |
+=====================+===============+=====================================================================+
| ``child-id``        | string        | ID of the module that displays to the student.                      |
+---------------------+---------------+---------------------------------------------------------------------+

.. this might be renamed to child_id

.. _Instructor_Event_Types:

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
