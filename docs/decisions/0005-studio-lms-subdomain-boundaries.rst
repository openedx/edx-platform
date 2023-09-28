Status
======

Proposed


Context
=======

The ``edx-platform`` repo contains both Studio and the LMS for Open edX. These
two systems roughly correspond to the Content Authoring and Learning subdomains,
but the precise separation of responsibilities is currently unclear in many
cases. This ADR is intended to clarify those boundaries and offer guidelines for
how developers should compose new functionality across these systems, as well as
providing a direction for migrating existing functionality over the long term.

Note that it is likely that we'll further separate content authoring (e.g.
content libraries) from course run administration (e.g. grading policy). It's
possible that both of these will evolve under the umbrella of what users see as
"Studio". Even if that happens, there will still be an architectural split
between the Content Authoring and Learning subdomains within that new Studio.


Decision
========

The high level guidelines for the interaction between the Content Authoring and
Learning subdomains currently represented by Studio and LMS are:

* Studio should not store Learner information.
* Studio and LMS should use different representations of content.
* Decouple content grouping concepts from user/learning grouping concepts.
* Studio Content data acts as an input to LMS policy and Learner Experience data.
* LMS data should not flow backward into Studio.
* Content Authoring changes require explicit publishing of versioned data.


Studio should not store Learner information.
--------------------------------------------

Studio's responsibility centers around the content itself. It should not store
information about students, which brings with it many other concerns around
data sensitivity and scale.


Studio and LMS should use different representations of content.
--------------------------------------------------------------------

Content authoring will require versioned storage of data, ownership tracking,
tagging, and other metadata. The LMS focuses on read-optimization at a much
higher scale. We've long suffered from added code complexity and performance
issues by trying to cover both usage patterns with ModuleStore.

We have already taken steps to create a read-optimized store in the form of
Block Transformers. We should continue this practice and encourage the LMS to
transform content at publish-time into whatever representation its various
systems (courseware, grading, scheduling, etc.) require to be performant.


Decouple content grouping concepts from user/learning grouping concepts.
------------------------------------------------------------------------

A common use case for course content is to show different bits of content to
different cohorts of users. For instance, a university might have a licensing
agreement that allows it to show a set of vidoes only to its own staff and
students, and not a wider MOOC audience. Studio needs to be able to annotate
this data somehow, but the list of available cohorts for a given course is
considered Learner information that may change from run to run.

We solve this by using a level of indirection. Studio doesn't map content into
Cohorts of students (an LMS concept). It maps content into Content Groups. The
LMS is then responsible for both the creation of Cohorts as well as the mapping
of Content Groups to Cohorts.

While this might sound a little cumbersome, it actually allows for a cleaner
separation of concerns. Content Groups describe what the content is: restricted
copyright, advanced material, labratory exercises, etc. Cohorts describe who is
consuming that material: on campus students, alumni, the general MOOC audience,
etc. The Content Group is an Authoring decision based on the properties of the
content itself. The Cohort mapping is a policy decision about the Learning
experience of a particular set of students.

Furthermore, the mapping of Content Groups to Cohorts is not 1:1. You could
decide that both on-campus students and alumni get the same content group
experience, while keeping those Cohorts separate for the purposes of other parts
of the LMS like forums discussions.

A more future looking example might be the interaction between Open edX
courseware and third party forum services. The fact that certain units are
marked as discussable topics might be a Content Authoring decision in Studio,
while the choice of which forum service those discussions happen in might be a
Learning decision in the LMS.


Studio Content data acts as an input to LMS policy and Learner Experience data.
-------------------------------------------------------------------------------

As courseware becomes more dynamic, certain concepts in the LMS are becoming
richer than their equivalent concepts in Studio. In these situations, we should
think of the data relationship as a one way flow of data from Studio to the LMS.
The LMS takes Studio data as an input that it can enrich, transform, or override
as necessary to create the desired student learning experience.

Content scheduling is a good example of this. In the early days of Open edX,
course teams would set start and due dates for subsections in Studio, and that
would be the end of it. Today, we have personalized schedules, individual due
date extensions, and more. The pattern we use to accomplish this is:

* Copy the schedule information from Studio to the LMS at the time a course is
  published, transforming it into a more easily queryable form in the process.
* Add additional data models in the LMS to support use cases like individual due
  date extensions and personalized rescheduling. This is currently handled by
  the edx_when app, developed in the edx-when repository.
* Remap field data so that XBlocks in the LMS runtime query this richer data
  model. Accessing an XBlock's ``start`` or ``due`` attribute in the Studio
  runtime continues to work with simple key/values in ModuleStore, but the LMS
  XBlock runtime will fetch those values from edx-when's in-process API.

This approach allows us to add flexibility to the LMS, while preserving
backwards compatibility with existing XBlock content.


LMS data should not flow backward into Studio.
----------------------------------------------

Since LMS concepts extend Studio ones, we don't want changes to flow backwards
from the LMS back into Studio. Some reasons:

* There is no guarantee that Studio course runs will be 1:1 with LMS course
  runs. In fact, one to many mappings of course runs already exist if CCX
  courses are enabled.
* A unidirectional data flow makes the system easier to debug and reason about.
* The OLX import/export process stays much simpler if it doesn't have to
  consider data that the LMS has added.


Content Authoring changes require explicit publishing of versioned data.
------------------------------------------------------------------------

Changes to content data should be marked with an explicit, versioned publishing
step. Many LMS systems update their representations of content data based on
publish signals from Studio today. Studio also needs to differentiate draft
changes authors want to make from changes that are ready for student use.

The LMS is permitted to modify the learning experience without any such explicit
publishing step. Deadlines may pass, blocking off student access to certain
parts of a course. Individual students may be placed into different teams or
cohorts, given extensions, re-graded, etc.


Goals
=====

* Developers will have a clearer understanding of where to build authoring and
  learning experience functionality.
* Improved separation of these subdomains will allow for easier debugging and
  better performance.
* Decoupling these subdomains will allow for more rapid interation and
  innovation.


Alternatives Considered
=======================

An early alternative approach (that periodically resurfaces) is to make the
content editing and publishing process happen in a much more integrated way. The
learning and authoring experience blend together so closely that the author is
essentially looking at the same interface as the student, supplemented with an
edit button to modify thing in-line.

This approach was rejected early on because:

* Authoring needs differed in the workflow and information that they had to
  surface to course authors.
* Separating the authoring and student experience allows multiple authoring
  systems (e.g. GitHub based OLX authoring).
* At various points, the content authoring experience has been owned by a
  different team than the learning experience.
