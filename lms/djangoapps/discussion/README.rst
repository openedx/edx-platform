Status: Maintenance

Responsibilities
================
The Discussion app powers the Open edX forums experience.

Direction: Move and Extract
===========================
Discussions related functionality is scattered across a number of places and should be better consolidated. Today we have:

* ``lms/djangoapps/discussion``
* ``openedx/core/djangoapps/django_comment_common``
* ``openedx/core/lib/xblock_builtin/xblock_discussion``

Ideally, what we want in the long term is for all of this extracted into a new repository that holds the code for both the inline discussion XBlock as well as all the Django apps.

That being said, it's not clear what the path forward for this app is. Forum functionality is something that has not been actively worked on for a while, and it's been suggested that we should remove this app altogether in favor of having better integration with other more established forum software. This decision is usually complicated by the desire to have tight integration with courseware and access to data for analytics.

Regardless, check with Product before undertaking any major refactoring work here.

Glossary
========

More Documentation
==================
