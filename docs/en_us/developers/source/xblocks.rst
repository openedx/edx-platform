Integrating XBlocks with edx-platform
=====================================

The edX LMS and Studio have several features that are extensions of the core XBlock
libraries (https://xblock.readthedocs.org). These features are listed below.

LMS
---

Runtime Features
~~~~~~~~~~~~~~~~

These are properties and methods available on ``self.runtime`` when a view or handler is executed by the LMS.

* anonymous_student_id: An identifier unique to the student in the particular course
  that the block is being executed in. The same student in two different courses
  will have two different ids.

* publish(event): Emit events to the surrounding system. Events are dictionaries with
  at least the key 'event_type', which identifies the other fields.

  TODO: Link to the authoritive list of event types.

In the future, these are likely to become more formal XBlock services (one related to users,
and the other to event publishing).

Class Features
~~~~~~~~~~~~~~

These are class attributes or functions that can be provided by an XBlock to customize behaviour
in the LMS.

* student_view (XBlock view): This is the view that will be rendered to display
  the XBlock in the LMS.
* has_score (class property): True if this block should appear in the LMS progress page.
* get_progress (method): See documentation in x_module.py:XModuleMixin.get_progress.
* icon_class (class property): This can be one of (``other``, ``video``, or ``problem``), and
  determines which icon appears in edx sequence headers. There is currently no way to provide
  a different icon.

Grading
~~~~~~~

To participate in the course grade, an XBlock should set ``has_score`` to ``True``, and
should ``publish`` a ``grade`` event whenever the grade changes. The ``grade`` event is a
dictionary of the following form::

    {
        'event_type': 'grade',
        'value': <number>,
        'max_value': <number>,
    }

The grade event represents a grade of ``value/max_value`` for the current user.

Restrictions
~~~~~~~~~~~~

* A block can't modify the value of any field with a scope where the ``user`` property
  is ``UserScope.NONE``.

Studio
------

Class Features
~~~~~~~~~~~~~~

* studio_view (XBlock.view): The view used to render an editor in Studio.

* non_editable_metadata_fields (property): A list of xblock.fields.Field objects that
  shouldn't be displayed in the default editing view for Studio.

Restrictions
~~~~~~~~~~~~

* A block can't modify the value of any field with a scope where the ``user`` property
  is not ``UserScope.NONE``.