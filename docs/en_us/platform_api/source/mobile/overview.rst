.. _edX Platform Mobile API Overview:

################################################
Mobile API Overview
################################################

Use the Mobile API to build mobile applications for students to view course
information and videos for courses on your instance of Open edX.

.. contents::
   :local:
   :depth: 1

******************************************
Mobile API Version and Status
******************************************

The Mobile API is currently at version 0.5 and is an alpha release. We plan on
making significant enhancements and changes to the API.

.. caution::
 As this is a new and rapidly evolving API, at this time edX does not
 guarantee forward compatibility. We encourage you to use and experiment with
 the API, while keeping in mind that endpoints might change.

*************************************
Mobile API Resources and Endpoints
*************************************

The Mobile API supports the following resources, tasks, methods, and
endpoints.

========================
Mobile API User Resource
========================

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get details about a user<Get User Details>`
     - GET 
     - /api/mobile/v0.5/users/{username}
   * - :ref:`Get course enrollments for a user<Get a User's Course Enrollments>`
     - GET 
     - /api/mobile/v0.5/users/{username}/course_enrollments/
   * - :ref:`Get a user's status in a course<Get or Change User Status in a Course>`
     - GET 
     - /api/mobile/v0.5/users/{username}/course_status_info/{course_id}
   * - :ref:`Change a user's status in a course<Get or Change User Status in a Course>`
     - PATCH 
     - /api/mobile/v0.5/rs/{username}/course_status_info/{course_id}

========================================
Mobile API Course Information Resource
========================================

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get updates for a course<Get Course Updates>`
     - GET
     - /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/updates   
   * - :ref:`Get handouts for a course<Get Course Handouts>`
     - GET
     - /api/mobile/v0.5/course_info/{organization}/{course_number}/{course_run}/handouts

=====================================
Mobile API Video Outlines Resource
=====================================

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get videos in a course<Get the Video List>`
     - GET
     - /api/mobile/v0.5/video_outlines/courses/{organization}/{course_number}/{course_run}
   * - :ref:`Get a video transcript<Get a Video Transcript>`
     - GET
     - /api/mobile/v0.5/video_outlines/transcripts/{organization}/{course_number}/{course_run}/{video ID}/{language code}