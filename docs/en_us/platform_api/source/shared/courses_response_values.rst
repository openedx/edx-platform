.. _Course:

Course
*******

* count (integer): The number of courses in the catalog.
* next (string): The URL for the next page of results.
* previous (string): The URL for the previous page of results.
* results (array): See :ref:`Results`.

.. _Results:

Results
*******

Parent: ``course``

A list of courses in the catalog.

* key (string): The unique identifier for the course.
* title (string): The title of the course.
* short_description (string): The short description of the course and its
  content.
* full_description (string): The long description of the course and its
  content.
* level_type (ENUM string): ---DESCRIPTION---
* subjects (array): Academic subjects that this course covers. See
  :ref:`Subjects`.
* prerequisites (array): Any courses a learner must complete before enrolling
  in the current course. ---This is in strikethrough text in the Google doc. Is
  it to be deleted?---
* expected_learning_items (array): ---This is in strikethrough text in the
  Google doc. Is it to be deleted?---
* image (array): The About page image for this course. See :ref:`image`.
* video (array): The course About video. See :ref:`Video`.
* owners (array): Institution that offers the course. See :ref:`Organization`.
* sponsors (array): Corporate sponsor for the course. See :ref:`Organization`.
* modified (datetime): The date and time the course was last modified.
* course_runs (array): Information about specific runs of the course. See
  :ref:`Course Runs`.
* marketing_url: ---DESCRIPTION---

.. _Course Runs:

course_runs
============

Parent: ``results``

A list of course runs for each course.

* course
* key (string): The unique identifier for the course.
* title (string): The title of the course.
* short_description (string): The short description of the course and its
  content.
* full_description (string): The long description of the course and its
  content.
* start (datetime): The course start date.
* end (datetime): The course end date.
* enrollment_start (datetime): The course enrollment start date.
* enrollment_end (datetime): The course enrollment end date.
* announcement ---Not in Google doc---
* image (array): See :ref:`Image`.
* video (array): The About video for this course run. See :ref:`Video`.
* seats (array): The available modes for this course. See :ref:`Seats`.
* content_language (string): The language for this course run.
* transcript_languages (array[string]): Languages in which video transcripts
  are available. ---This is in strikethrough text in the Google doc. Is
  it to be deleted?---
* instructors (array): See :ref:`Person`. ---Not in Google doc---
* staff (array): Information about the course staff. See :ref:`Person`.
* pacing_type (ENUM string): The pacing of the course. May be **self-paced** or
  **instructor-paced**.
* min_effort (integer): ---Not in Google doc. A different value, "effort", is
  in strikethrough text. Is this to be deleted? ---
* max_effort (integer): ---Not in Google doc. A different value, "effort", is
  in strikethrough text. Is this to be deleted? ---
* modified (datetime): The date and time the course was last modified.

.. _Image:

image
======

The following ``image`` objects have identical response values.

* ``image`` (parent: ``course``, ``course_runs``, ``video``)
* ``logo_image`` (parent: ``organization``)
* ``profile_image`` (parent: ``person``)

The ``image`` object has the following response values.

* src (string): The URL where the image is located.
* description (string): A description of the image.
* height (integer): The height of the image in pixels.
* width (integer): The width of the image in pixels.

.. _Organization:

organization
==============

The following ``organization`` objects have identical response values.

* ``owners`` (parent: ``results``)
* ``sponsors`` (parent: ``results``)

The ``organization`` object has the following response values.

* key (string): The unique ID for the organization.
* name (string): The name of the organization.
* description (string): A description of the organization.
* logo_image (array): See :ref:`Image`.
* homepage_url (string): The URL of the organization's home page.

.. _Person:

person
=========

The following ``person`` objects have identical response values.

* ``instructor`` (parent: ``course_runs``)
* ``staff`` (parent: ``course_runs``)

The ``person`` object has the following response values.

* key (string): A unique identifier for the instructor or staff member.
* name (string): The first and last name of the instructor or staff member.
* title (string): The official title of the instructor or staff member.
* bio (string): Biographical information about the instructor or staff member.
* profile_image (array): See :ref:`Image`.

.. _Prerequisites:

Prerequisites
==================

Parent: ``results``

Any courses a learner must complete before enrolling in the current course.

* name (string): ---The name of the prerequisite course. This is in
  strikethrough text in the Google doc. Is it to be deleted?---

.. _Seats:

Seats
=========

Parent: ``course_runs``

* type (string): The course mode or modes that the course offers. Possible
  values are ``audit``, ``verified``, or ``professional education``.
* price (string): The cost in USD of a verified certificate, a professional
  education certificate, or academic credit for the course.
* currency (string): The currency in which the course accepts payment. This
  value must be ``USD``.
* upgrade_deadline (string): The deadline for learners to upgrade from the
  audit track to the verified certificate track.
* credit_provider (string): The institution that offers academic credit for
  learners who pass the course.
* credit_hours (integer): The number of credit hours that learners who pass the
  course earn.

.. _Subjects:

Subjects
=========

Parent: ``results``

Academic subjects that this course covers.

* name (string): Name of a subject, such as "computer science" or "history".

**Possible values:**

::

    Architecture
    Art & Culture
    Biology & Life Sciences
    Business & Management
    Chemistry
    Communication
    Computer Science
    Data Analysis & Statistics
    Design
    Economics & Finance
    Education & Teacher Training
    Electronics
    Energy & Earth Sciences
    Engineering
    Environmental Studies
    Ethics
    Food & Nutrition
    Health & Safety
    History
    Humanities
    Language
    Law
    Literature
    Math
    Medicine
    Music
    Philanthropy
    Philosophy & Ethics
    Physics
    Science
    Social Sciences

.. _Video:

Video
=========

Parent: ``course``, ``course_runs``

* src (string): URL for the video.
* description (string): Description of the video.
* image (array): See :ref:`Image`.
