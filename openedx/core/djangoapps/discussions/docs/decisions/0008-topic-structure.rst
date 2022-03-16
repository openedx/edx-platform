Migrating Topic Structures to XBlocks to the new Mechanism
==========================================================


Status
------

Draft


Context
-------

A new mechanism for configuration topic is being introduced that moves away
from using XBlocks to add discussions to units. In the new mechanism if
in-context topics are enabled, all Units other than those in graded sections
will automatically get a topic assigned that has the same name as the unit.
There is a setting to allow topics for graded sections as well. Finally, there
is an option to override these automatic topic assignment so you can pick which
units get a topic and which don't.

The hierarchy of topics is now determined by the course itself, based on the
sections and subsection instead of categories specified for the course.

This ADR documents the various existing topic structures, and how they can be
represented or migrated to the new course topic mechanism being introduced.

Migrations
----------

The difficulty of migration depends how many of the following hold true.

1. The course does not have multiple discussion blocks in a single unit.
2. The course does not have any discussion blocks in exams.
3. The discussion subcategory (topic) in the block matches the name of the unit.
4. The discussion category in the block matches the subsection name in which
   discussion block was added.

1. Simplest Migration: Fully compatible original structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If all of the above hold true then we can simply copy over the existing
discussion IDs, mark the units that had discussion blocks as discussable,
and unmark the units that didn't have discussion blocks.

Note: It's OK if multiple units use the same discussion ID.

Course Structure:

.. code-block::

    Section 1
        Subsection 1.1
            Unit 1.1.1
                Discussion Block id=discussion111 category=Subsection 1.1 subcategory=Unit 1.1.1
            Unit 1.1.2
                Discussion Block id=discussion112 category=Subsection 1.1 subcategory=Unit 1.1.2
    Section 2
        Subsection 2.1
            Unit 2.1.1
                Discussion Block id=discussion211 category=Subsection 2.1 subcategory=Unit 2.1.1
            Unit 2.1.2
                Discussion Block id=discussion211 category=Subsection 2.1 subcategory=Unit 2.1.2

The old and new topic structure:

.. code-block::

    Subsection 1.1
        Unit 1.1.1
        Unit 1.1.2
    Subsection 2.1
        Unit 2.1.1
        Unit 2.1.2

2. Harder Migration: Mismatch in course and topic structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the final criterion doesn't hold true, i.e the category names don't match
the subsection name, then the final structure will not match the original
structure, however, the topic names will not change.

If the third condition doesn't hold true either then the topic names will
change but the data can still be retained.

Course Structure:

.. code-block::

    Section 1
        Subsection 1.1
            Unit 1.1.1
                Discussion Block id=discussion111 subcategory=Unit 1.1.1 category=Category 1
            Unit 1.1.2
                Discussion Block id=discussion112 subcategory=Unit 1.1.2 category=Category 1
    Section 2
        Subsection 2.1
            Unit 2.1.1
                Discussion Block id=discussion211 subcategory=Unit 2.1.1 category=Category 2
            Unit 2.1.2
                Discussion Block id=discussion211 subcategory=Unit 2.1.2 category=Category 3
            Unit 2.1.3
                Discussion Block id=discussion213 subcategory=Homework category=Category 1

The old topic structure:

.. code-block::

    Category 1
        Unit 1.1.1
        Unit 1.1.2
        Homework
    Category 2
        Unit 2.1.1
    Category 3
        Unit 2.1.2

The new topic structure:

.. code-block::

    Subsection 1.1
        Unit 1.1.1
        Unit 1.1.2
    Subsection 2.1
        Unit 2.1.1
        Unit 2.1.2
        Unit 2.1.3

2. Harder Migration: Units in exam sections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the units are present in exam sections, they will simply not get topics
in the new topic configuration mechanism. This is no longer supported. If
migrating an existing course to the new topic structure, any posts in the old
topic in the exam unit will be inaccessible.

However, it is possible to have a disabled/archived topic created for such
topics from where moderators can move posts to other topics.

2. Harder Migration: Units in exam sections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Having multiple topics in a single unit is no longer supported. It was possible
to add multiple discussion blocks to a single unit. Something like this is no
longer possible.

The only automatic remedy that can be made available is to merge these topics
into a single topic. If any posts already exist in the old topic, they can be
moved to the new topic.

Decision
--------

