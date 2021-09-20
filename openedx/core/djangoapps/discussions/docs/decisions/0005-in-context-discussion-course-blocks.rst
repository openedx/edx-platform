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
already used by the learning MFE. The learning MFE can then directly
embed this link in an iframe as a sidebar.

For example, when the discussion link is requested using
`requested_fields=discussions_embed_url` it will return roughly the
following:

.. code-block:: JSON

    {
        ...
        "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471": {
            "id": "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471",
            "block_id": "vertical_98cf62510471",
            "lms_web_url": "http...",
            "legacy_web_url": "http...",
            "student_view_url": "http...",
            "discussions_embed_url": "http://localhost:2002/discussions/course-v1:edX+DemoX+Demo_Course/topics/zooming-diagrams/"
            "type": "vertical",
            "display_name": "Zooming Diagrams"
        },
        ...
    }

For units that don't have a linked discussion, no link will be returned.

The new discussions experience includes a setting called 
`discussions_group_at_subsection` to group discussions at the subsection 
level instead of the unit level. By default this setting is disabled and
the sidebar next to a unit will only show threads from that unit. 
However, if this setting is enabled then the MFE should show threads 
related to all the units from the subsection in the sidebar. 

If this setting is enabled, then the blocks API will return a link for 
the entire subsection. The MFE can accomodate for this in the UI by
presenting it in a different way if need be. 

E.g.

.. code-block:: JSON

    {
        ...
        "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471": {
            "id": "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_98cf62510471",
            "block_id": "vertical_98cf62510471",
            "lms_web_url": "http...",
            "legacy_web_url": "http...",
            "student_view_url": "http...",
            "discussions_embed_url": "http://localhost:2002/discussions/course-v1:edX+DemoX+Demo_Course/category/lesson-2-lets-get-interactive/"
            "type": "vertical",
            "display_name": "Zooming Diagrams"
        },
        ...
    }
