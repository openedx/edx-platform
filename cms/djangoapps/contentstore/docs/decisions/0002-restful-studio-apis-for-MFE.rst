0002: Expose Existing Studio APIs for use in MFEs
=================================================


Status
------

Proposed

Context
-------

New MFEs which are in development, need to use studio APIs to interact with course tabs
and advanced course settings. Currently these endpoints don't have RESTful APIs that
can be used by MFEs using OAuth2 or similar.

Currently the course tabs page at `<studio_url>/tabs/<course_key>` has a single
`old-style functional view`_ that serves as both the view for the HTML page and the
JSON-based API for post requests. It also only supports session-based auth. While
this works well currently, for MFE consumption this is not ideal. The
`advanced course settings`_ view is in a similar situation.

.. _old-style functional view: https://github.com/openedx/edx-platform/blob/49296005db7397e1a45e2864d93d39cf790a5fce/cms/djangoapps/contentstore/views/tabs.py#L27
.. _advanced course settings: https://github.com/openedx/edx-platform/blob/49296005db7397e1a45e2864d93d39cf790a5fce/cms/djangoapps/contentstore/views/course.py#L1367

To avoid disrupting the existing studio views that might still be needed for the next
few releases, we need to maintain these existing views while also enabling MFEs to
perform operations currently only enabled by these views.

Decision
--------

We will expose the existing studio APIs under a new versioned endpoint. These
endpoints will support the new JWT/OAuth2 authentication mechanisms supported by
MFEs.

The existing views can be kept as-is, and only the authentication layer will be
changed. These APIs can be versioned as v0 since the format of these APIs can be
changed to better suit MFEs in future revisions, and might potentially be
organised differently in the future.

The first APIs to get this treatment are:

1. The tabs APIs currently available at `<studio_url>/tabs/<course_key>`
   will now also be exposed at `<studio_url>/api/contentstore/v0/tabs/<course_key>`.
2. The advanced course settings APIs currently available at `<studio_url>/settings/advanced/<course_key>`
   will now also be exposed at `<studio_url>/api/contentstore/v0/advanced_settings/<course_key>`


Consequences
------------

The `Course Authoring MFE`_, and other MFEs will be able to use these APIs making it
possible to port existing studio pages to their new UX in Course Authoring MFE and
elsewhere.

There are some adjustments that may be needed for these APIs soon, such as the
ability to use the tabs APIs from MFEs, currently GET is only supported with HTML
not JSON.

For the short-term though, these APIs will unblock progress on new MFE UX without
without needing to write entirely new APIs.

.. _Course Authoring MFE: https://github.com/openedx/frontend-app-course-authoring/
