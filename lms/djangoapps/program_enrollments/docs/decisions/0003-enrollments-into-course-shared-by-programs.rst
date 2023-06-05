Enrollments Into A Course Shared By Multiple Programs
-----------------------------------------------------

Status
======

Accepted (circa March 2020)


Context
=======

For the spring term 2020 (Starting Jan 6th), Georgia Tech has created 3
different Masters programs on edX. One such Masters program is named
"Other Master Program". This program is linked to all the courses
offered by both the Cybersecurity and Data Analytics programs.
This created a situation where every Georgia Tech's course run is
referenced by two different Masters program at least. We need a
mechanism to properly control the integrity of student enrollment data
in light of the cross reference.

The scope of this decision is related to how API would react to enrollment
requests to a course for a single user, but from more than one programs.
The decision also covers the scenario where a learner needs to move
program enrollment from one program to another program.

Decisions
=========

We update the field "Course Enrollment" of the "ProgramCourseEnrollment"
model from OneToOne field to a Foreign Key field.
We also implemented logic to prevent two "active" "programCourseEnrollment"
records to be written into data store for the same user for the same course
across any number of affliated programs. This means, only 0 or 1 "active"
enrollment for a learner and the enrolled course can exist in our data store
at any given time.

Consequences
============

API caller who wants to enroll learner into the course of Program 1 would
succeed, and then the call to enroll the same learner into the same course
of program 2 would result in "conflicted" status and fail. The only way
to enroll learner into course of program 2 is to cancel the enrollment of
the learner into course of program 1.
With this change, we will have multiple ProgramCourseEnrollment model
referencing the same student_courseenrollment record. But only one
of those ProgramCourseEnrollment record should be in "active" status

Alternatives
============

We also considered, but rejected the following possibilities:

1) Instead of preventing the ProgramCourseEnrollment to have another
   "active" record for the same learner and course, update the only such
   ProgramCourseEnrollment record to point to the ProgramEnrollment
   where the latest request is made for.
   This is rejected because the update would make the transition of program
   course enrollment records opague. The data model is setup with assumption
   where program course enrollment records are children of program enrollment
   records. This solution would break such assumption.

2) Allow multiple "active" ProgramCourseEnrollment for the same learner
   and course for multiple ProgramEnrollments
   This makes database integraty difficult to enforce. It might generate multiple
   duplicate records that confuses our system. This option would also result in
   inactive ProgramCourseEnrollment pointing at an active student_courseenrollment
   record, thus making it confusing.
