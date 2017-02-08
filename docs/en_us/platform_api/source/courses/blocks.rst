.. _Courses API Blocks Resource:

########################################
Courses API Blocks Resource
########################################

With the Courses API **Blocks** resource, you can complete the
following tasks.


.. contents::
   :local:
   :depth: 1

.. _Get a list of the course blocks in a course:

****************************************
Get a List of Course Blocks in a Course
****************************************

The endpoint to get a list of course blocks in a course is
``/api/courses/v1/blocks/`` with required ``course_id`` parameter.

=====================
Use Case
=====================

Get a list of course blocks in a specified course. Response results depend on
the viewing user's permissions level within a course, as well as group
membership and individual allowances (such as due date extensions), if any.

=====================
Request Format
=====================

GET /api/courses/v1/blocks/?course_id=<course_id>

Example:

GET /api/courses/v1/blocks/?course_id=edX%2FDemoX%2FDemo_Course
&all_blocks=true&requested_fields=graded,format,student_view_multi_device


.. _Blocks Query Parameters:

=====================
Query Parameters
=====================

* all_blocks: (boolean) Provide a value of ``true`` to return all
  blocks, including those that are visible only to specific learners (for
  example, based on group or cohort membership, or randomized content from
  content libraries). Returns all blocks only if the requesting user has course
  staff permissions. If ``all_blocks`` is not specified, you must specify the
  username for the user whose course blocks are requested.

* block_counts: (list) Specify the types of blocks for which to return a
  count. Example: ``block_counts=video,problem``.

* block_types_filter: (list) Specify the types of blocks to be included in
  results. Values are the names of any XBlock type in the system, for example:
  ``sequential``, ``vertical``, ``html``, ``problem``, ``video`` or
  ``discussion``. Example: ``block_types_filter=problem,html``.

* course_id: (string, required) The URL-encoded ID of the course whose block
  data you are requesting. Example: ``course_id=edX%2FDemoX%2FDemo_Course``.

* depth: (integer or ``all``) Specify how far in the course blocks hierarchy
  to traverse down. A value of ``all`` specifies the entire hierarchy. The
  default value is ``0``. Example: ``depth=all``.

* requested_fields: (list) Specify the fields to return for each block, in
  addition to ``id``, ``type``, and ``display_name``, which are always
  returned. For the list of possible fields, see the fields listed under
  ``blocks`` in the :ref:`Blocks Response Values` section. Example:
  ``requested_fields=graded,format,student_view_multi_device``.

* return_type: (string) Specify the data type in which the block data is
  returned. Supported values are ``dict`` and ``list``. The default value is
  ``dict``.

* student_view_data: (list)  Specify the types of blocks for which to return
  the ``student_view_data`` response value, which consists of a JSON
  representation of the block's data. Example: ``student_view_data=video``.

* username: (string) Required, unless ``all_blocks`` is specified. Specify the
  username for the user whose course blocks are requested. Only users with
  course staff permissions can specify other users' usernames. If a username
  is specified, results include blocks that are visible to that user,
  including those based on group or cohort membership or randomized content
  assigned to that user. Example: ``username=anjali``.


.. _Blocks Response Values:

=====================
Response Values
=====================

The following fields are returned with a successful response.

* root: The ID of the root node of the requested course block structure.

* blocks: A dictionary or list, based on the value of the ``return_type``
  query parameter. Maps block usage IDs to a collection of information about
  each block, as described in the following fields.

  * id: (string) The usage ID of the block.

  * type: (string) The type of block. Values are the names of any XBlock type
    in the system, including custom blocks. Examples are: ``course``,
    ``chapter``, ``sequential``, ``vertical``, ``html``, ``problem``,
    ``video``, and ``discussion``.

  * display_name: (string) The display name of the block.

  * children: (list) If the block has child blocks, an ordered list of IDs of
    the child blocks. Returned only if ``children`` is included in the
    ``requested_fields`` query parameter.

  * block_counts: (dict) For each block type specified in the ``block_counts``
    query parameter, the aggregate number of blocks of that type within the
    root block and all of its descendants. For example, if you specify
    ``block_counts=video,problem`` as a query parameter, in the
    ``block_counts`` response value the number of video blocks and problem
    blocks in the specified block and in its children, is returned.

  * graded: (boolean) Whether or not the block or any of its descendants is
    graded. Returned only if ``graded`` is included in the ``requested_fields``
    query parameter.

  * format: (string) The assignment type of the block. Possible values can be
    ``Homework``, ``Lab``, ``Midterm Exam``, and ``Final Exam``. Returned only if
    ``format`` is included in the ``requested_fields`` query parameter.

  * student_view_data: (dict) The JSON data for this block, if the specified
    block type implements the ``student_view_data`` method. The JSON data can
    be used to natively render the XBlock. Returned only if the
    ``student_view_data`` query parameter contains this block's type. See also
    ``student_view_multi_device`` and ``student_view_url``.

  * student_view_multi_device: (boolean) This value indicates whether or not
    the HTML of the student view that is rendered at the ``student_view_url``
    supports responsive web layouts, touch-based inputs, and interactive state
    management for a variety of device sizes and types, including mobile and
    touch devices. Returned only if ``student_view_multi_device`` is included
    in the ``requested_fields`` query parameter.

  * student_view_url: (string) The URL to retrieve the HTML rendering of the
    block's student view. The HTML can include CSS and Javascript code. This
    field can be used in combination with the ``student_view_multi_device``
    field to determine whether a block can be viewed on a device. This URL can
    be used as a fallback if the ``student_view_data`` for this block type is
    not supported by the client or by the block.

  * lms_web_url: (string) The URL to the navigational container of the XBlock
    on the web LMS. This URL can be used as a fallback if the
    ``student_view_data`` and ``student_view_url`` fields are not supported.

  * lti_url: (string) The block URL for an LTI consumer. Returned only if the
    ``ENABLE_LTI_PROVIDER`` Django setting is set to ``True``.


============================================================================
Example Response Showing a List of Course Blocks in a Specified Course
============================================================================

The following example response is returned from this request:

GET /api/courses/v1/blocks/?course_id=edX/DemoX/Demo_Course&all_blocks=true
&block_counts=video,html,problem&requested_fields=graded,format,student_view_data,
student_view_url,student_view_multi_device&student_view_data=video,html,problem

Only the top level block in the course is returned, because the ``depth``
parameter was not specified.

.. code-block:: json

 {
    "root": "i4x://edX/DemoX/course/Demo_Course",
    "blocks": {
        "i4x://edX/DemoX/course/Demo_Course": {
            "display_name": "edX Demonstration Course",
            "graded": false,
            "student_view_url": "https://courses.edx.org/xblock/i4x://edX/DemoX/
             course/Demo_Course",
            "student_view_multi_device": false,
            "lms_web_url": "https://courses.edx.org/courses/edX/DemoX/Demo_Course/
             jump_to/i4x://edX/DemoX/ course/Demo_Course",
            "type": "course",
            "id": "i4x://edX/DemoX/course/Demo_Course",
            "block_counts": {
                "problem": 23,
                "html": 32,
                "video": 5
            }
        }
    }
 }


.. _Get a list of the course blocks in a block tree:

*********************************************
Get a List of Course Blocks in a Block Tree
*********************************************

The endpoint to get a list of course blocks in a specified block tree is
``/api/courses/v1/blocks/{usage_id}/``.

=====================
Use Case
=====================

Get a list of course blocks in a specified block tree. Response results depend
on the specified user's permissions level within a course, as well as group
membership and individual allowances (such as due date extensions), if any.

=====================
Request Format
=====================

GET /api/courses/v1/blocks/{usage_id}/

Example:

GET /api/courses/v1/blocks/i4x%3A%2F%2FedX%2FDemoX%2Fvertical
%2F2152d4a4aadc4cb0af5256394a3d1fc7?all_blocks=true


=====================
Query Parameters
=====================

:ref:`Query parameters<Blocks Query Parameters>` for this endpoint are the
same as those for :ref:`Get a list of the course blocks in a course`.


=====================
Response Values
=====================

:ref:`Response values<Blocks Response Values>` for this endpoint are the same
as those for :ref:`Get a list of the course blocks in a course`.


================================================================
Example Response Showing a List of Course Blocks in a Block Tree
================================================================

The following example response is returned from this request:

GET /api/courses/v1/blocks/i4x%3A%2F%2FedX%2FDemoX%2Fvertical
%2F2152d4a4aadc4cb0af5256394a3d1fc7?all_blocks=true


.. code-block:: json

 {
    "root": "i4x://edX/DemoX/vertical/2152d4a4aadc4cb0af5256394a3d1fc7",
    "blocks": {
        "i4x://edX/DemoX/discussion/e5eac7e1a5a24f5fa7ed77bb6d136591": {
            "display_name": "",
            "lms_web_url": "https://courses.edx.org/courses/edX/DemoX/Demo_Course/
             jump_to/i4x://edX/DemoX/discussion/e5eac7e1a5a24f5fa7ed77bb6d136591",
            "type": "discussion",
            "id": "i4x://edX/DemoX/discussion/e5eac7e1a5a24f5fa7ed77bb6d136591",
            "student_view_url": "https://courses.edx.org/xblock/i4x://edX/DemoX/
             discussion/e5eac7e1a5a24f5fa7ed77bb6d136591"
        },
        "i4x://edX/DemoX/vertical/2152d4a4aadc4cb0af5256394a3d1fc7": {
            "display_name": "Pointing on a Picture",
            "lms_web_url": "https://courses.edx.org/courses/edX/DemoX/Demo_Course/
             jump_to/i4x://edX/DemoX/vertical/2152d4a4aadc4cb0af5256394a3d1fc7",
            "type": "vertical",
            "id": "i4x://edX/DemoX/vertical/2152d4a4aadc4cb0af5256394a3d1fc7",
            "student_view_url": "https://courses.edx.org/xblock/i4x://edX/DemoX/
             vertical/2152d4a4aadc4cb0af5256394a3d1fc7"
        },
        "i4x://edX/DemoX/problem/c554538a57664fac80783b99d9d6da7c": {
            "display_name": "Pointing on a Picture",
            "lms_web_url": "https://courses.edx.org/courses/edX/DemoX/Demo_Course/
             jump_to/i4x://edX/DemoX/problem/c554538a57664fac80783b99d9d6da7c",
            "type": "problem",
            "id": "i4x://edX/DemoX/problem/c554538a57664fac80783b99d9d6da7c",
            "student_view_url": "https://courses.edx.org/xblock/i4x://edX/DemoX/
             problem/c554538a57664fac80783b99d9d6da7c"
       }
    }
 }
