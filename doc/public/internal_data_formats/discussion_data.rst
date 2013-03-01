######################
Discussion Forums Data
######################
Discussions in edX are stored in a MongoDB database as collections of JSON documents.

The primary collection holding all posts and comments written by users is `contents`. There are two types of objects stored here, though they share much of the same structure. A `CommentThread` represents a comment that opens a new thread -- usually a student question of some sort. A `Comment` is a reply in the conversation started by a `CommentThread`.

*****************
Shared Attributes
*****************

The attributes that `Comment` and `CommentThread` objects share are listed below.

`_id`
-----
  The 12-byte MongoDB unique ID for this collection. Like all MongoDB IDs, they are monotonically increasing and the first four bytes are a timestamp. 

`_type`
-------
  `CommentThread` or `Comment` depending on the type of object.

`anonymous`
-----------
  If true, this `Comment` or `CommentThread` will show up as written by anonymous, even to those who have moderator privileges in the forums.

`anonymous_to_peers`
--------------------
  The idea behind this field was that `anonymous_to_peers = true` would make the the comment appear anonymous to your fellow students, but would allow the course staff to see who you were. However, that was never implemented in the UI, and only `anonymous` is actually used. The `anonymous_to_peers` field is always false.

`at_position_list`
------------------
  No longer used. Child comments (replies) are just sorted by their `created_at` timestamp instead. 

`author_id`
-----------
  The user who wrote this. Corresponds to the user IDs we store in our MySQL database as `auth_user.id`

`body`
------
  Text of the comment in Markdown. UTF-8 encoded.

`course_id`
-----------
  The full course_id of the course that this comment was made in, including org and run. This value can be seen in the URL when browsing the courseware section. Example: `BerkeleyX/Stat2.1x/2013_Spring`

`created_at`
------------
  Timestamp in UTC. Example: `ISODate("2013-02-21T03:03:04.587Z")`

`updated_at`
------------
  Timestamp in UTC. Example: `ISODate("2013-02-21T03:03:04.587Z")`

`votes`
-------
  Both `CommentThread` and `Comment` objects support voting. `Comment` objects that are replies to other comments still have this attribute, even though there is no way to actually vote on them in the UI. This attribute is a dictionary that has the following inside:

* `up` = list of User IDs that up-voted this comment or thread.
* `down` = list of User IDs that down-voted this comment or thread (no longer used).
* `up_count` = total upvotes received.
* `down_count` = total downvotes received (no longer used).
* `count` = total votes cast.
* `point` = net vote, now always equal to `up_count`.

A user only has one vote per `Comment` or `CommentThread`. Though it's still written to the database, the UI no longer displays an option to downvote anything.

*************
CommentThread
*************
The following fields are specific to `CommentThread` objects. Each thread in the forums is represented by one `CommentThread`.

`closed`
--------
  If true, this thread was closed by a forum moderator/admin.

`comment_count`
---------------
  The number of comment replies in this thread. This includes all replies to replies, but does not include the original comment that started the thread. So if we had::

    CommentThread: "What's a good breakfast?"
      * Comment: "Just eat cereal!"
      * Comment: "Try a Loco Moco, it's amazing!"
        * Comment: "A Loco Moco? Only if you want a heart attack!"
        * Comment: "But it's worth it! Just get a spam musubi on the side."

  In that exchange, the `comment_count` for the `CommentThread` is `4`.

`commentable_id`
----------------
  We can attach a discussion to any piece of content in the course, or to top level categories like "General" and "Troubleshooting". When the `commentable_id` is a high level category, it's specified in the course's policy file. When it's a specific content piece (e.g. `600x_l5_p8`, meaning 6.00x, Lecture Sequence 5, Problem 8), it's taken from a discussion module in the course.

`last_activity_at`
------------------
  Timestamp in UTC indicating the last time there was activity in the thread (new posts, edits, etc). Closing the thread does not affect the value in this field. 

`tags_array`
------------
  Meant to be a list of tags that were user definable, but no longer used.

`title`
-------
  Title of the thread, UTF-8 string.

*******
Comment
*******
The following fields are specific to `Comment` objects. A `Comment` is a reply to a `CommentThread` (so an answer to the question), or a reply to another `Comment` (a comment about somebody's answer). It used to be the case that `Comment` replies could nest much more deeply, but we later capped it at just these three levels (question, answer, comment) much in the way that StackOverflow does.

`endorsed`
----------
  Boolean value, true if a forum moderator or instructor has marked that this `Comment` is a correct answer for whatever question the thread was asking. Exists for `Comments` that are replies to other `Comments`, but in that case `endorsed` is always false because there's no way to endorse such comments through the UI.

`comment_thread_id`
-------------------
  What `CommentThread` are we a part of? All `Comment` objects have this.

`parent_id`
-----------
  The `parent_id` is the `_id` of the `Comment` that this comment was made in reply to. Note that this only occurs in a `Comment` that is a reply to another `Comment`; it does not appear in a `Comment` that is a reply to a `CommentThread`.

`parent_ids`
------------
  The `parent_ids` attribute appears in all `Comment` objects, and contains the `_id` of all ancestor comments. Since the UI now prevents comments from being nested more than one layer deep, it will only ever have at most one element in it. If a `Comment` has no parent, it's an empty list.
