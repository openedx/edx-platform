Status
======

Proposed


Context
=======

XBlock was first envisioned as a nearly all-encompassing, dynamic system. How
many points is a problem worth? Call its ``max_score`` method. When is it due?
Check for the ``due`` attribute. What other XBlock content does it contain? Ask
the XBlock for its children. The course content was an object graph of XBlocks
that were free to implement this sort of functionality in different and
potentially very powerful ways, allowing for rapid experimentation in grading,
navigation, etc. This was especially important for edx-platform, which started
life as a rapidly developed prototype for courseware.

Unfortunately, such an open ended system made it extremely difficult to make
guarantees about performance and stability. For instance, many assessment XBlock
types will return a ``1`` for its ``max_score`` method, but ``ProblemBlock``
will introspect its XML to determine how many response fields it has, and use
that figure. In cases where these problems had to run sandboxed code, getting
the maximum possible score might involve forking an entire new process and
making IPC calls to it. If an XBlock wanted to determine its maximum score by
making a blocking HTTP request to a third-party service, there is nothing
stopping it from doing so.

This made operations that traversed many XBlocks (such as navigation, grading,
or sequence rendering) especially unpredictable, as the cost of getting the most
basic information could vary by literally six orders of magnitude. Any one
misbehaving XBlock could sabotage the entire request.

There were also downstream complications with allowing XBlocks so much freedom.
Systems such as analytics could not make basic assumptions about course
structure and problem metadata. If XBlocks wanted to render different child
XBlocks to different users, or make a problem worth more to users named "jarvis"
on Wednesday afternoons, it was free to do so. But the analytics system couldn't
easily introspect all this internal XBlock logic, meaning that it had to either
make assumptions that could be incorrect, or dynamically query XBlocks in a way
that was unpredictably expensive.

To address these issues, we were forced to sharply constrain what XBlocks were
permitted to do in practice. This stabilized the site and brought performance to
a tolerable (though not great) level, but at a significant cost. Numerous low
level optimizations and access patterns complicated the code, while at the same
time compromising some of the expressive power of XBlocks. Many of the API calls
that *look* dynamic were actually constrainted with unstated assumptions–maximum
scores are assumed to be consistent across all user, courses are assumed to have
a Course → Section → Subsection structure, etc.

Reaching beyond these constraints is still possible, but the results are
unpredictable. The LMS will still render unusual navigational structures if you
import it directly via OLX, but mobile clients and analytics will likely break.
You can define different max scores for different students on the same problem,
but you will likely see bugs in various places where those scores are cached and
displayed.

Largely because of these issues, the XBlock runtime gradually shifted away from
the all-encompassing role it once played in courseware:

* Grading and Scheduling became distinct subsystems with their own data models
  and APIs. Instead of these systems synchronously pulling data from XBlock at
  query time, we push XBlock data into these systems and query them using their
  own APIs. This has vastly increased the operational stability of the platform.
* LTI support has been extracted from ``LtiConsumerXBlock``, so that LTI
  integration can happen outside the XBlock runtime.
* There is active planning to add limited QTI support to Open edX.
* The ``learning_sequence`` application is being developed to take over Section
  and Sequence level navigation, decoupling those concepts from the XBlock
  runtime in the LMS.
* There is a strong interest in creating more adaptive and composable courseware
  experiences which are difficult to do within the constraints of the XBlock
  runtime.
* There have been early conversations around what a successor to XBlock might
  look like, though no development work has begun.

At the same time, it's important to note that there are hundreds of XBlocks in
existence and a vast quantity of valuable content that has been written for
those XBlocks. Preserving the viability of this content is critical to the
success of Open edX.


Decision
========

XBlocks have provided us a fantastic source of innovative content, at the cost
of many operational issues. We'll proceed in a way that allows us to preserve
the most valuable parts of the XBlock framework, while developing a more
performant, XBlock-agnostic layer of extensible LMS APIs.

In concrete terms:

* XBlocks will continue to be supported at the Unit and individual module level
  (e.g. ProblemBlock, VideoBlock). XBlocks will execute in a container that only
  has their Unit (VerticalBlock). They will be allowed to query sibling blocks,
  but will no longer be allowed to freely query their ancestors to get at
  content in other units, sequences, or the root Course block.
* Responsibility for higher level navigation across collections of content (i.e.
  Sequences, Sections, and Courses) will move to dedicated applications that
  will have their own, XBlock-agnostic data models and APIs.
* A new application will be created to make an XBlock-agnostic model of Units in
  the LMS, similar to the work that is currently being done around Sequences in
  ``learning_sequences``.
* OLX will continue to be supported, including the OLX for navigational
  structures. They will be mapped to new LMS models and APIs, instead of the
  XBlock runtime.
* XBlock will eventually become a peer runtime to other systems for pluggable
  course content.
* Navigation will have its own set of dedicated, pluggable APIs that are
  separate from the rendering of individual Units.


Goals
=====

1. Enable rapid innovation in courseware content and navigation.
2. Preserve backwards compatibility with existing XBlock content.
3. Improve the reliability, security, and performance of the platform.


Consequences
============

A DEPR will be created for removing the ability for XBlocks to reach outside
their unit in various ways, such as calling ``get_parent`` above the Unit level
or ``get_course`` to get the root Course XBlock. This would likely happen in the
Lilac timeframe. XBlocks that are part of the default install of Open edX will
be updated as necessary.


Background
==========

The following give a much more detailed account of the various challenges we've
faced with the XBlock framework over the years:

* `XBlock Lessons Learned <https://docs.google.com/document/d/1Flj2MS5Neyw6ilSMPdjHqP_4ATX3Qs_pcQdLJIpeSLA/edit?usp=sharing>`_
* `XBlock Lessons: Plugin Performance and Grading <https://engineering.edx.org/xblock-lessons-plugin-performance-and-grading-2f85a1d6fb2a>`_
* `XBlock Field Data Complexity <https://medium.com/@dormsbee/xblock-lessons-field-data-complexity-2ef32d961b97>`_
