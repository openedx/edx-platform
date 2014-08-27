.. _Discussion Forums Data:

######################
Discussion Forums Data
######################

EdX discussion data is stored as collections of JSON documents in a MongoDB database. MongoDB is a document-oriented, NoSQL database system. Documentation can be found at the mongodb_ web site.

..  _mongodb: http://docs.mongodb.org/manual/

In the data package, discussion data is delivered in a .mongo file, identified by organization and course, in this format: edX-*organization*-*course*-*source*.mongo. 

The primary collection that holds all of the discussion posts written by users is "contents". Two different types of objects are stored, representing the three levels of interactions that users can have in a discussion. 

* A ``CommentThread`` represents the first level of interaction: a post that opens a new thread, often a student question of some sort. 

* A ``Comment`` represents both the second and third levels of interaction: a response made directly to the conversation started by a ``CommentThread`` is a ``Comment``. Any further contributions made to a specific response are also in ``Comment`` objects.

A sample of the field/value pairs that are in the mongo file, and descriptions of the attributes that these two types of objects share and that are specific to each type, follow.

In addition to these collections, events are also emitted to track specific user activities. See :ref:`forum_events`.

*********
Samples
*********

Two sample rows, or JSON documents, from a ``.mongo`` file of discussion data
follow. 

----------------------------------------
CommentThread Document Example
----------------------------------------

The JSON documents that include discussion data are delivered in a compact,
machine-readable format that can be difficult to read at a glance.

.. code-block:: json

 { "_id" : { "$oid" : "50f1dd4ae05f6d2600000001" }, "_type" : "CommentThread", "anonymous" : 
 false, "anonymous_to_peers" : false, "at_position_list" : [], "author_id" : "NNNNNNN", 
 "author_username" : "AAAAAAAAAA", "body" : "Welcome to the edX101 forum!\n\nThis forum will 
 be regularly monitored by edX. Please post your questions and comments here. When asking a 
 question, don't forget to search the forum to check whether your question has already been 
 answered.\n\n", "closed" : false, "comment_count" : 0, "commentable_id" : "i4x-edX-edX101-
 course-How_to_Create_an_edX_Course", "course_id" : "edX/edX101/How_to_Create_an_edX_Course", 
 "created_at" : { "$date" : 1358028106904 }, "last_activity_at" : { "$date" : 1358134464424 }, 
 "tags_array" : [], "title" : "Welcome to the edX101 forum!", "updated_at" : { "$date" : 
 1358134453862 }, "votes" : { "count" : 1, "down" : [], "down_count" : 0, "point" : 1, "up" : 
 [ "48" ], "up_count" : 1 } }

If you use a JSON formatter to "pretty print" this document, a version that is
more readable is produced.

.. code-block:: json

  {
    "_id": {
      "$oid": "50f1dd4ae05f6d2600000001"
    },
    "_type": "CommentThread",
    "anonymous": false,
    "anonymous_to_peers": false,
    "at_position_list": [
    
    ],
    "author_id": "NNNNNNN",
    "author_username": "AAAAAAAAAA",
    "body": "Welcome to the edX101 forum!\n\nThis forum will be regularly monitored by edX. Please 
    post your questions and comments here. When asking a question, don't forget to search the  
    forum to check whether your question has already been answered.\n\n",
    "closed": false,
    "comment_count": 0,
    "commentable_id": "i4x-edX-edX101-course-How_to_Create_an_edX_Course",
    "course_id": "edX\/edX101\/How_to_Create_an_edX_Course",
    "created_at": {
      "$date": 1358028106904
    },
    "last_activity_at": {
      "$date": 1358134464424
    },
    "tags_array": [
    
    ],
    "title": "Welcome to the edX101 forum!",
    "updated_at": {
      "$date": 1358134453862
    },
    "votes": {
      "count": 1,
      "down": [
      
      ],
      "down_count": 0,
      "point": 1,
      "up": [
        "48"
      ],
      "up_count": 1
    }
  }

----------------------------------------
Comment Document Example
----------------------------------------

.. code-block:: json

 { "_id" : { "$oid" : "52e54fdd801eb74c33000070" }, "votes" : { "up" : [], "down" : [], 
 "up_count" : 0, "down_count" : 0, "count" : 0, "point" : 0 }, "visible" : true, 
 "abuse_flaggers" : [], "historical_abuse_flaggers" : [], "parent_ids" : [], "at_position_list" : 
 [], "body" : "I'm hoping this Demonstration course will help me figure out how to take the 
 course I registered for. I am just auditing the course, but I want to benefit from it as much 
 as possible, as I am extremely interested in it.\n", "course_id" : "edX/DemoX/Demo_Course", 
 "_type" : "Comment", "endorsed" : false, "anonymous" : false, "anonymous_to_peers" : false, 
 "author_id" : "NNNNNNN", "comment_thread_id" : { "$oid" : "52e4e880c0df1fa59600004d" }, 
 "author_username" : "AAAAAAAAAA", "sk" : "52e54fdd801eb74c33000070", "updated_at" : 
 { "$date" : 1390759901966 }, "created_at" : { "$date" : 1390759901966 } }

When pretty printed, this comment looks like this:

.. code-block:: json

  {
    "_id": {
      "$oid": "52e54fdd801eb74c33000070"
    },
    "votes": {
      "up": [
      
      ],
      "down": [
      
      ],
      "up_count": 0,
      "down_count": 0,
      "count": 0,
      "point": 0
    },
    "visible": true,
    "abuse_flaggers": [
    
    ],
    "historical_abuse_flaggers": [
    
    ],
    "parent_ids": [
    
    ],
    "at_position_list": [
    
    ],
    "body": "I'm hoping this Demonstration course will help me figure out how to take the 
    course I registered for. I am just auditing the course, but I want to benefit from it 
    as much as possible, as I am extremely interested in it.\n",
    "course_id": "edX\/DemoX\/Demo_Course",
    "_type": "Comment",
    "endorsed": false,
    "anonymous": false,
    "anonymous_to_peers": false,
    "author_id": "NNNNNNN",
    "comment_thread_id": {
      "$oid": "52e4e880c0df1fa59600004d"
    },
    "author_username": "AAAAAAAAAA",
    "sk": "52e54fdd801eb74c33000070",
    "updated_at": {
      "$date": 1390759901966
    },
    "created_at": {
      "$date": 1390759901966
    }
  }

*****************
Shared Fields
*****************

Descriptions of the fields that are present for both ``CommentThread`` and ``Comment`` objects follow.

--------------------
_id
--------------------
  The 12-byte MongoDB unique ID for this collection. Like all MongoDB IDs, the IDs are monotonically increasing and the first four bytes are a timestamp. 

--------------------
_type
--------------------
  ``CommentThread`` or ``Comment`` depending on the type of object.

--------------------
anonymous
--------------------
  If true, this ``CommentThread`` or ``Comment`` displays in the user interface as written by "anonymous", even to those who have course staff or discussion administration roles in the course. 

--------------------
anonymous_to_peers
--------------------
  If true, this ``CommentThread`` or ``Comment`` displays in the user interface as written by "anonymous" to students, but  course staff and discussion administrators see the author's username. 

--------------------
at_position_list
--------------------
  No longer used. Child comments (replies) are sorted by their ``created_at`` timestamp only. 

--------------------
author_id
--------------------
  Identifies the user who wrote this. Corresponds to the user IDs stored in the MySQL database as ``auth_user.id``.

--------------------
author_username
--------------------
  The username of the person who wrote the discussion post or comment. 

--------------------
body
--------------------
  Text of the comment in Markdown. UTF-8 encoded.

--------------------
course_id
--------------------
  The full course_id of the course that this comment was made in, including org and run. This value can be seen in the URL when browsing the courseware section. Example: ``BerkeleyX/Stat2.1x/2013_Spring``.

.. 12 Feb 14, Sarina: not yet relevant but with splitmongo changes course_id conventions will change. may be worth discussing with Don et al as to when we expect these changes to land and how to document.  

--------------------
created_at
--------------------
  Timestamp in UTC. Example: ``ISODate("2013-02-21T03:03:04.587Z")``.

.. FOR-482 open to research inconsistency between the data actually in the data package and this example and description.

--------------------
updated_at
--------------------
  Timestamp in UTC. Example: ``ISODate("2013-02-21T03:03:04.587Z")``.

.. FOR-482 open to research inconsistency between the data actually in the data package and this example and description.

--------------------
votes
--------------------
  Both ``CommentThread`` and ``Comment`` objects support voting. In the user interface, students can vote for posts (``CommentThread`` objects) and for responses, but not for the third-level comments made on responses. All ``Comment`` objects still have this attribute, even though there is no way to actually vote on the comment-level items in the UI. This attribute is a dictionary that has the following items inside:

  * up = list of User IDs that up-voted this comment or thread.
  * down = list of User IDs that down-voted this comment or thread (no longer used).
  * up_count = total upvotes received.
  * down_count = No longer used. Total downvotes received.
  * count = total votes cast.
  * point = net vote, now always equal to up_count.

A user only has one vote per ``Comment`` or ``CommentThread``. Though it's still written to the database, the UI no longer displays an option to downvote anything.

**************************
CommentThread Fields
**************************

The following fields are specific to ``CommentThread`` objects. Each thread in the discussion forums is represented by one ``CommentThread``.

--------------------
closed
--------------------
  If true, this thread was closed by a discussion forum moderator or admin.

--------------------
comment_count
--------------------
  The number of comment replies in this thread. This includes all responses and replies, but does not include the original post that started the thread. So for this exchange::

    CommentThread: "What's a good breakfast?"
      * Comment: "Just eat cereal!"
      * Comment: "Try a Loco Moco, it's amazing!"
        * Comment: "A Loco Moco? Only if you want a heart attack!"
        * Comment: "But it's worth it! Just get a spam musubi on the side."

  The ``comment_count`` for this ``CommentThread`` is **4**.

--------------------
commentable_id
--------------------
  A course team can attach a discussion to any piece of content in the course, or to top level categories like "General" and "Troubleshooting". When the discussion is a top level category it is specified in the course's policy file, and the ``commentable_id`` is formatted like this: "i4x-edX-edX101-course-How_to_Create_an_edX_Course". When the discussion is a specific component in the course, the ``commentable_id`` identifies that component: "d9f970a42067413cbb633f81cfb12604".

--------------------
last_activity_at
--------------------
  Timestamp in UTC indicating the last time there was activity in the thread (new posts, edits, etc). Closing the thread does not affect the value in this field. 

.. FOR-482 open to research inconsistency between the data actually in the data package and this example and description.

--------------------
tags_array
--------------------
  No longer used. 

  **History**: Intended to be a list of user definable tags.

--------------------
title
--------------------
  Title of the thread. UTF-8 string.

********************
Comment Fields
********************

The following fields are specific to ``Comment`` objects. A ``Comment`` is either a response to a ``CommentThread`` (such as an answer to the question), or a reply to another ``Comment`` (a comment about somebody's answer). 

**History**: It used to be the case that ``Comment`` replies could nest much more deeply, but this was later capped at just these three levels (post, response, comment) much in the way that StackOverflow does.

--------------------
visible
--------------------
  Not used.

--------------------
abuse_flaggers
--------------------
  Records the user id of each user who selects the **Report Misuse** flag for a ``Comment`` in the user interface. Stores an array of user ids if more than one user flags the ``Comment``. This is empty if no users flag the ``Comment``. 

----------------------------------------
historical_abuse_flaggers
----------------------------------------
  If a discussion moderator removes the **Report Misuse** flag from a ``Comment``, all user IDs are removed from the ``abuse_flaggers`` field and then written to this field.

--------------------
endorsed
--------------------
  Boolean value, true if a forum moderator or instructor has marked that this ``Comment`` is a correct answer for whatever question the thread was asking. Exists for Comments that are replies to other Comments, but in that case ``endorsed`` is always false because there's no way to endorse such comments through the UI.

--------------------
comment_thread_id
--------------------
  Identifies the ``CommentThread`` that the ``Comment`` is a part of. 

--------------------
parent_id
--------------------
  Applies only to comments made to a response. In the example given for ``comment_count`` above, "A Loco Moco? Only if you want a heart attack!" is a comment that was made to the response, "Try a Loco Moco, it's amazing!"

  The ``parent_id`` is the ``_id`` of the response-level ``Comment`` that this ``Comment`` is a reply to. Note that this field is only present in a ``Comment`` that is a reply to another ``Comment``; it does not appear in a ``Comment`` that is a reply to a ``CommentThread``.

--------------------
parent_ids
--------------------
  The ``parent_ids`` field appears in all ``Comment`` objects, and contains the ``_id`` of all ancestor comments. Since the UI now prevents comments from being nested more than one layer deep, it will only ever have at most one element in it. If a ``Comment`` has no parent, it is an empty list.

--------------------
sk
--------------------
  A randomly generated number that drives a sorted index to improve online performance.

