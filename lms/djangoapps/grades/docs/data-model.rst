Grades Data Model
-----------------

.. contents::

Course Grades
-------------

**Table Name**: grades_persistentcoursegrade

**Table Description**: Persistent values for learners' course grades.

**Indices from Uniqueness Constraint**: ('course_id', 'user_id')

 * course_id
 * course_id, user_id

**Additional Indices:**

 * user_id
 * course_id, passed_timestamp
 
 **Fields:**
 
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| Field name              | Type         | Description                                                                                                                                                                                                                                   | Include in Data Package |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| course_id               | CourseKey    | Course key of the containing course.                                                                                                                                                                                                          | Y                       |
|                         |              | Example:                                                                                                                                                                                                                                      |                         |
|                         |              | course-v1:org+course+run (for new-type courses) or                                                                                                                                                                                            |                         |
|                         |              | org/course/run (for old-type courses)                                                                                                                                                                                                         |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| user_id                 | Integer      | User ID of the learner.                                                                                                                                                                                                                       | Y                       |
|                         |              | Example: 41446                                                                                                                                                                                                                                |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| course_edited_timestamp | DateTime     | Last edited timestamp of the course when the grade was computed.                                                                                                                                                                              | N                       |
|                         |              | Currently used for debugging purposes only.                                                                                                                                                                                                   |                         |
|                         |              | Example: 2016-12-21 15:50:23.645000                                                                                                                                                                                                           |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| course_version          | String (255) | The version number of the course in the Split Modulestore when the grade was computed.                                                                                                                                                        | N                       |
|                         |              | Currently used for debugging purposes only.                                                                                                                                                                                                   |                         |
|                         |              | Note: The old Mongo modulestore doesn't support versions and so this field will be NULL for those courses. The "course_edited_timestamp" field should be used instead to understand dated information of the course content.                  |                         |
|                         |              | Example: 58ff632f00d9e7501e0148c4                                                                                                                                                                                                             |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| grading_policy_hash     | String (255) | A SHA-1 digest of the course grading policy.  It allows us to detect and update grades whenever the policy changes.                                                                                                                           | Y                       |
|                         |              | Example: NiGhcAFSrpyijXbow/XKE1Cp1GA=                                                                                                                                                                                                         |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| percent_grade           | Float        | The learner's calculated course grade as a decimal percentage, per grading policy.                                                                                                                                                            | Y                       |
|                         |              | Example: 0.91 (means 91%)                                                                                                                                                                                                                     |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| letter_grade            | String (255) | The learner's calculated course grade as a letter value (e.g., A→D, Pass), per grading policy.  If the learner's grade is Fail or F, this cell value is empty.                                                                                | Y                       |
|                         |              | Example: Pass or A                                                                                                                                                                                                                            |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| passed_timestamp        | DateTime     | Time when the learner first passed the course.  If this cell value is empty, the learner never passed the course.  If this cell value is non-empty but the letter_grade value is empty, the learner transitioned from passing to not passing. | Y                       |
|                         |              | Note: There will be a lag in time from when the learner submitted the problem that caused them to pass and when the grade was computed (asynchronously by the platform post external grader, ORA grading, etc).                               |                         |
|                         |              | Example: 2017-05-02 15:51:04.395055                                                                                                                                                                                                           |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| created                 | DateTime     | Time the course grade was first calculated for this user for this course.                                                                                                                                                                     | Y                       |
|                         |              | Note: Backfilled grades will have this value set to the time the grade was eventually computed and backfilled.                                                                                                                                |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+
| modified                | DateTime     | Time the course grade was last updated for this user for this course.                                                                                                                                                                         | Y                       |
|                         |              | Note: Backfilled grades will have this value set to the time the grade was eventually computed and backfilled.                                                                                                                                |                         |
+-------------------------+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+

**Expected Read Use Cases:**

+--------------------------------------------------------------------------------------+-----------------------------+---------------------------------------+
| Use case for reading from the table                                                  | Feature/team                | Required Indices                      |
|                                                                                      |                             | (to be completed by engineering team) |
+--------------------------------------------------------------------------------------+-----------------------------+---------------------------------------+
| Progress page displays learner's course grade, along with other grade breakdown info | LMS Progress Page           | course_id, user_id                    |
+--------------------------------------------------------------------------------------+-----------------------------+---------------------------------------+
| Course dashboard displays learner's course grade for each enrolled course            | LMS Student Dashboard       | user_id                               |
+--------------------------------------------------------------------------------------+-----------------------------+---------------------------------------+
| Grade report generates CSV with course grade for each learner in the course          | LMS Grade Report            | course_id                             |
+--------------------------------------------------------------------------------------+-----------------------------+---------------------------------------+
| Measure course completion statistics.                                                | Analytics/Course Completion | course_id, passed_timestamp           |
+--------------------------------------------------------------------------------------+-----------------------------+---------------------------------------+


Subsection Grades
-----------------

There are two tables that work in conjunction for storing subsection grades: Subsection Grade and Visible Blocks.

Subsection Grade Table
^^^^^^^^^^^^^^^^^^^^^^

**Table Name:** grades_persistentsubsectiongrade

**Table Description:** Persistent values for learners' subsection grades.

**Indices from Uniqueness Constraint:** ('course_id', 'user_id', 'usage_key')

course_id
course_id, user_id
course_id, user_id, usage_key

**Additional Indices:**

visible_blocks_hash

**Fields:**

+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| Field name               | Type          | Description                                                                                                                                                                                       | Include in DP |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| course_id                | CourseKey     | Course key of the containing course.                                                                                                                                                              | Y             |
|                          |               | Example:                                                                                                                                                                                          |               |
|                          |               | course-v1:org+course+run (for new-type courses) or                                                                                                                                                |               |
|                          |               | org/course/run (for old-type courses)                                                                                                                                                             |               |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| course_version           | String (255)  | The version number of the course in the Split Modulestore when the grade was computed.                                                                                                            | N             |
|                          |               | Currently used for debugging purposes only.                                                                                                                                                       |               |
|                          |               | Example: 58ff632f00d9e7501e0148c4                                                                                                                                                                 |               |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| created                  | DateTime      | Time the subsection grade was first calculated for this user for this subsection.                                                                                                                 | Y             |
|                          |               | Note: Backfilled grades will have this value set to the time the grade was eventually computed and backfilled.                                                                                    |               |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| earned_all               | Float         | The user's aggregated "total_weighted_earned" score in the subsection, calculated by summing all "weighted_earned" values of all problems in the subsection.                                      | Y             |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| earned_graded            | Float         | The user's aggregated "total_weighted_earned" score in the subsection, calculated by summing all "weighted_earned" values of all graded problems in the subsection.                               | Y             |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| first_attempted          | DateTime      | Time of the user's first attempt at a problem in the subsection. If the user has not attempted a subsection, the entry for that subsection will be absent.                                        | Y             |
|                          |               | Note: Backfilled grades will use best-effort to derive a value for this - by computing a minimum of all the "created" dates on the attempted scores for the available problems in the subsection. |               |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| modified                 | DateTime      | Time the subsection grade was last updated for this user for this subsection.                                                                                                                     | Y             |
|                          |               | Note: Backfilled grades will have this value set to the time the grade was eventually computed and backfilled.                                                                                    |               |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| possible_all             | Float         | The aggregated "total_weighted_possible" score in the subsection, calculated by summing all "weighted_possible" values of all problems in the subsection.                                         | Y             |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| possible_graded          | Float         | The aggregated "total_weighted_possible" score in the subsection, calculated by summing all "weighted_possible" values of all graded problems in the subsection.                                  | Y             |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| subtree_edited_timestamp | DateTime      | Last edited timestamp of the content of the subsection or any of its descendants when the grade was computed.                                                                                     | N             |
|                          |               | Currently used for debugging purposes only.                                                                                                                                                       |               |
|                          |               | Example: 2016-12-21 15:50:23.645000                                                                                                                                                               |               |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| usage_key                | UsageKey      | Usage key of the subsection. (This has other aliases: 'module_id', 'location')                                                                                                                    | Y             |
|                          |               | Example:                                                                                                                                                                                          |               |
|                          |               | block-v1:org+course+run+type@sequential+block@1234 (for new courses) or                                                                                                                           |               |
|                          |               | i4x://org/course/sequential/1234 (for old-type courses)                                                                                                                                           |               |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| user_id                  | Integer       | User ID of the learner.                                                                                                                                                                           | Y             |
|                          |               | Example: 41446                                                                                                                                                                                    |               |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| visible_blocks           | VisibleBlocks | Foreign key to the grades_visibleblocks table.                                                                                                                                                    | N             |
+--------------------------+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+

**Expected Read use Cases:**

+------------------------------------------------------------------------------------------+---------------------+---------------------------------------+
| Use case for reading from the table                                                      | Feature/team        | Required Indices                      |
|                                                                                          |                     | (to be completed by engineering team) |
+------------------------------------------------------------------------------------------+---------------------+---------------------------------------+
| Compare with previous grade to see whether it should be conditionally updated            | Rescore to Increase | course_id, user_id, usage_key         |
+------------------------------------------------------------------------------------------+---------------------+---------------------------------------+
| Detailed grade report generates CSV with subsection grade for each learner in the course | LMS Grade Report    | course_id                             |
+------------------------------------------------------------------------------------------+---------------------+---------------------------------------+
| Progress page displays learner's subsection grade breakdown                              | LMS Progress Page   | course_id, user_id                    |
+------------------------------------------------------------------------------------------+---------------------+---------------------------------------+

Visible Blocks Table
^^^^^^^^^^^^^^^^^^^^
**Table Name:** grades_visibleblocks

**Table Description:** Stores an ordered list of visible blocks within a subsection for a learner at the time of computing the subsection grade.  It is expected that multiple learners will share access to the same list of visible blocks and hence this data is stored in a separate table so it can be referred to by multiple rows in the Subsection Grade table.

**Indices from Uniqueness Constraint:** ('hashed)

 * hashed
 
**Additional Indices:**

 * course_id

**Fields:**

+-------------+--------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| Field name  | Type         | Description                                                                                                                                                                                                                                                                                                                                                                                                                           | Include in DP |
+-------------+--------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| course_id   | CourseKey    | Course key of the containing course.                                                                                                                                                                                                                                                                                                                                                                                                  | N             |
+-------------+--------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| hashed      | String (100) | A SHA1 hash of the blocks_json value.                                                                                                                                                                                                                                                                                                                                                                                                 | N             |
+-------------+--------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+
| blocks_json | LongText     | A JSON with the following information:                                                                                                                                                                                                                                                                                                                                                                                                | N             |
|             |              | version: An integer representing the version number of the data format.                                                                                                                                                                                                                                                                                                                                                               |               |
|             |              | course_key: Serialized CourseKey of the containing course.                                                                                                                                                                                                                                                                                                                                                                            |               |
|             |              | blocks: An ordered list of serialized UsageKeys of all blocks that are accessible to the user within a particular subsection.                                                                                                                                                                                                                                                                                                         |               |
|             |              | Note: The blocks field contains a list of usage keys of all blocks within a subsection that are visible to the user at the time of computing the user's subsection grade.  The value changes whenever users' access to content within the subsection changes: cohort assignment change, role change, course team adds/removes unit/problem, etc. When changed, a new row is created in the table with a corresponding new hash value. |               |
+-------------+--------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+


Problem Scores
--------------
A learner's score for a specific problem is stored in either of 2 SQL tables, depending on the type of problem.

Courseware Student Module
^^^^^^^^^^^^^^^^^^^^^^^^^

**Table Name:** courseware_studentmodule

**Table Description:** A general-purpose storage for user-specific state for any xBlock/xModule (not just problem-types).  In addition to user-state, separate fields exist to store "earned" and "possible" grades for scorable blocks.

**Indices from Uniqueness Constraint: ('student', 'module_id', 'course_id')**

* student
* student, module_id
* student, module_id, course_id

**Additional Indices:**

* module_type
* module_id
* course_id
* grade
* done
* created
* modified

**Fields:**

+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name  | Type            | Description                                                                                                                                                                                             |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| student     | User            | Foreign key to the User table.                                                                                                                                                                          |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| state       | String          | Free formed string that is contextually interpreted by the xBlock in question.                                                                                                                          |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| module_type | String (32)     | Block type of the xBlock in question.  For example: problem, video, html, chapter, etc.                                                                                                                 |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| module_id   | UsageKey (255)  | Usage key of the xBlock in question.                                                                                                                                                                    |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| modified    | DateTime        | Time the row was last modified.                                                                                                                                                                         |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| max_grade   | Float           | The problem's "raw_possible" score at the time the user submitted the problem. Persisting this value here allows for the problem's content to change without affecting the user's score on the problem. |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| grade       | Float           | The user's "raw_earned" score on the problem.                                                                                                                                                           |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| done        | String          | Possible values: Not Applicable, Finished, Incomplete                                                                                                                                                   |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| created     | DateTime        | Time the row was created.                                                                                                                                                                               |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| course_id   | CourseKey (255) | Course key of the containing course of the xBlock in question.                                                                                                                                          |
+-------------+-----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


ORA Submissions
^^^^^^^^^^^^^^^

**Table Name:** submissions_score

**Table Description:** One of the tables amongst the suite of tables used for ORA submissions.  This particular table stores the scores for ORA problems.

**Indices from Uniqueness Constraint: ('id')**

 * id
 
**Additional Indices:**

 * student_item_id
 * submission_id
 * created_at
 
**Fields:**

+-----------------+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field name      | Type             | Description                                                                                                                                                                                                   |
+-----------------+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| created_at      | DateTime         | Time the row was created.                                                                                                                                                                                     |
+-----------------+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| points_earned   | Positive Integer | The user's "weighted_earned" score on the problem.                                                                                                                                                            |
+-----------------+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| points_possible | Float            | The problem's "weighted_possible" score at the time the user submitted the problem. Persisting this value here allows for the problem's content to change without affecting the user's score on the problem.  |
|                 |                  | Note, since points_earned and points_possible reflect the weighted values, the problem's weight is not applied for scores in the Submissions table when grades are aggregated.                                |
+-----------------+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| reset           | Boolean          | Indicates that the score in this row should reset the current highest score.                                                                                                                                  |
+-----------------+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| student_item    | StudentItem      | Foreign key to the submissions_studentitem table.                                                                                                                                                             |
+-----------------+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| submission      | Submission       | Foreign key to the submissions_submission table.                                                                                                                                                              |
+-----------------+------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+



