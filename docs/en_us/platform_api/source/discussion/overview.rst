.. _EdX Platform Discussion API Overview:

################################################
Discussion API Overview
################################################

Use the edX Platform Discussion API to view the discussion topics, threads, and
comments for a course. You can also create, modify, and delete threads and
comments.

You can use the Discussion API for browser and mobile applications.

********************************************
Discussion API Version 1.0
********************************************

The Discussion API is currently at version 1.0. EdX plans to enhance this API.

**********************************************
Discussion API Resources and Endpoints
**********************************************

The Discussion API supports the following tasks, methods, and endpoints.

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get the list of discussion threads in a course 
       <Get the List of Discussion Threads in a Course>`
     - GET
     - /api/discussion/v1/courses/{course_id}
   * - :ref:`Get the list of discussion topics in a course
       <Get the List of Discussion Topics in a Course>`
     - GET
     - /api/discussion/v1/course_topics/{course_id}
   * - :ref:`Get the list of threads for a course 
       <Get or Update the List of Threads for a Course>`
     - GET
     - /api/discussion/v1/threads/?course_id={course_id}
   * - :ref:`Post a new thread
       <Get or Update the List of Threads for a Course>`
     - POST
     - /api/discussion/v1/threads{"course_id":*ID*,"topic_id":*ID*,"type":*type*,"title":*title text*,"raw_body":*body text*}
   * - :ref:`Modify a thread
       <Get or Update the List of Threads for a Course>`
     - PATCH
     - /api/discussion/v1/threads/thread_id{"raw_body": *edited body text*}
   * - :ref:`Delete a thread
       <Get or Update the List of Threads for a Course>`
     - DELETE
     - /api/discussion/v1/threads/{thread_id}
   * - :ref:`Get the list of comments for a thread 
       <Get or Update the List of Comments for a Thread>`
     - GET
     - /api/discussion/v1/comments/?thread_id=*ID*
   * - :ref:`Post a new comment
       <Get or Update the List of Comments for a Thread>`
     - POST
     - /api/discussion/v1/comments/{"thread_id":*ID*,"raw_body":*body text*}
   * - :ref:`Modify a comment
       <Get or Update the List of Comments for a Thread>`
     - PATCH
     - /api/discussion/v1/comments/comment_id{"raw_body":*edited body text*}
   * - :ref:`Delete a comment
       <Get or Update the List of Comments for a Thread>`
     - DELETE
     - /api/discussion/v1/comments/{comment_id}


