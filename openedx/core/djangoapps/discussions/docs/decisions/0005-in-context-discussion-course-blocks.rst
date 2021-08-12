Making Linked In-Context Discussions Available to MFEs
======================================================


Status
------

Proposal


Context
-------

In the `ADR 0004 <./0004-in-context-discussions-linking.rst>`_ we investigated
how to link a discussion to a unit. We also need some way to make these linked
discussions available to the frontend so they can display those in-context
discussions in the correct view.


Requirements
------------

An API to access linked discussions for a Unit.


Decision
--------

A direct link to the topic that needs to be embedded can be generated
by edx-platform and provided to MFEs via the course blocks API which is
already is used by the learning MFE. The learning MFE can then directly
embed this link in a sidebar.

For example, when the discussion link is requested using
`requested_fields=discussions_embed_url` it will return roughly the
following:

.. code-block:: JSON

    {
        ...
        "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471": {
            "id": "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471",
            "block_id": "vertical_98cf62510471",
            "lms_web_url": "http://localhost:18000/courses/course-v1:edX+DemoX+Demo_Course/jump_to/block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471",
            "legacy_web_url": "http://localhost:18000/courses/course-v1:edX+DemoX+Demo_Course/jump_to/block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471?experience=legacy",
            "student_view_url": "http://localhost:18000/xblock/block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471",
            "discussions_embed_url": "http://localhost:2002/discussions/course-v1:edX+DemoX+Demo_Course/topics/zooming-diagrams/"
            "type": "vertical",
            "display_name": "Zooming Diagrams"
        },
        ...
    }

For units that don't have a linked discussion, no link will be returned.

The new discussions experience includes a setting to group discussions at
the subsection level instead of the unit level. This setting will show all
threads related to a subsection in the sidebar if enabled. If this setting
is enabled, then the blocks API will return a link for a the entire
subsection. The discussions MFE will be responsible for checking that this
course has the setting enabled, and will show an alternative UI in that case.

E.g.

.. code-block:: JSON

    {
        ...
        "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471": {
            "id": "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471",
            "block_id": "vertical_98cf62510471",
            "lms_web_url": "http://localhost:18000/courses/course-v1:edX+DemoX+Demo_Course/jump_to/block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471",
            "legacy_web_url": "http://localhost:18000/courses/course-v1:edX+DemoX+Demo_Course/jump_to/block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471?experience=legacy",
            "student_view_url": "http://localhost:18000/xblock/block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471",
            "discussions_embed_url": "http://localhost:2002/discussions/course-v1:edX+DemoX+Demo_Course/category/lesson-2-lets-get-interactive/"
            "type": "vertical",
            "display_name": "Zooming Diagrams"
        },
        ...
    }

The discussions MFE will then display all the threads in this category.
