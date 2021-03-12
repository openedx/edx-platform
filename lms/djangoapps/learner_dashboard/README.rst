Status: Maintenance

Responsibilities
================

This Django app hosts dashboard pages used by edX learners. The intent is for
this Django app to include the following dashboard tabs:

 - Courses
 - Programs

Direction: Deprecate
====================
This is being replaced by new UI that is in active development.  New functionality should not be added here.

Glossary
========

Courses
-------

The learner-facing dashboard listing active and archived enrollments. The
current implementation of the dashboard resides in
``common/djangoapps/student/``.

Programs
--------

A page listing programs in which the learner is engaged. The page also shows
learners' progress towards completing the programs. Programs are structured
collections of course runs which culminate into a certificate.


More Documentation
==================

Implementation
^^^^^^^^^^^^^^

The ``views`` module contains the Django views used to serve the Program listing
page. The corresponding Backbone app is in the
``edx-platform/static/js/learner_dashboard``.

Configuration
^^^^^^^^^^^^^

In order to turn on the Programs tab, you need to update the ``Programs API
Config`` object in the lms Django admin. Make sure you set the values
``Enabled``, ``Do we want to show program listing page`` and ``Do we want to
show xseries program advertising`` to be true
