Status: Maintenance

Responsibilities
================
The edxnotes app is responsible for displaying parts of the Notes UI to students in different parts of the LMS, as well as figuring out whether Notes is enabled for a particular situation. The bulk of the actual work in storing the notes is done by a separate service (see the edx-notes-api repo).

Direction: Extract into Plugin
==============================
Notes needs to insert a new tab into the LMS courseware, as well as wrap/decorate the courseware XBlock output so that it can add annotation capability to it. Both of these can now be done via plugins (decorating XBlock output can be done with XBlock Asides), and this app should be extracted into a separate repository.

This app is also currently proxying some requests through the LMS instead of hitting its service endpoint directly. It should instead always let the user's browser hit the edx-notes-api service directly.

The edxnotes app also has an endpoint to get JWT tokens that the edx-notes-api will accept. This should be removed, and the edx-notes-api service converted to use the OAuth2 + JWT Cookie approach detailed in the `Transport JWT in HTTP Cookies <https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0009-jwt-in-session-cookie.rst>`_ decision record for ``oauth_dispatch``.

Glossary
========

More Documentation
==================
