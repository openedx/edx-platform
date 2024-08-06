Course Models
#############

Status
******

Accepted

Implementation pending

Decision
********

edx-platform will have a first-class model to represent the idea of a *catalog course*.
If we think of multiple runs of the same course to all derive from one
conceptual "course", the catalog course is what will represent that conceptual course.

Context
*******

The term "course" in Open edX is ambiguous, referring to one of two things:

1. An individual *run* of a course which is authored in Studio and published to LMS. Here, we call this the **CourseRun**. In edx-platform, it is modeled by the **CourseOverview**.
2. A logical course *catalog* entry that may be marketed, sold, awarded as a credential, and bundled into programs. Here, we call this the **CatalogCourse**.

Every one CatalogCourse maps to N CourseRuns.

Historically, CatalogCourses  have been inferred from the names of courses with the
runs removed (eg. `course-v1:AximX/Eng101` could be a catalog course with multiple runs
(`course-v1:AximX/Eng101:2024H1`, `course-v1:AximX/Eng1012024H2`, etc)). Having the catalog course explicitly defined as a new model has multiple benefits.
runs removed (eg. "AximX/Eng101" could be a catalog course with multiple runs
(2024H1, 2024H2, etc)). Having this explicitly defined as a new model has
multiple benefits.

* Relationships between course runs can be defined explicitly instead of implicitly.

  * Currently this information is either implied (via course key) or requested from
    course-discovery. In the case of edx-platform, it loads the entire course-discovery
    database into a cache.

* A list of all courses can be easily queried both internally and via the rest API.

* Catalog courses can be explicitly mapped to organizations rather than implicitly.

* The door is opened to also persist program or course bundle data in the future.
  This will stop `programs-related features from breaking whenever memcached is reset <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/catalog/docs/decisions/001-programs-cache.rst>`_.

* Org → Course → Course Runs mappings don't have to follow implicit naming
  Conventions and associations can be changed more easily.

Rejected Alternatives
*********************

Rely on course-discovery for CatalogCourse
==========================================

The course-discovery service already has some models to represent this and we
could rely on it directly but it also contains a lot of representations that
are specific to the edx.org process and it's not valuable to spin up the
course-discovery service just to get this information for most operators.

As long as any local data can be updated from course-discovery if
course-discovery is setup in an environment, we should not have any conflicts
between the two locations.

Essentially, if an operator has course-discovery enabled, the models here would
be a persisted cache of the relevant information.  However, if
course-discovery is not enabled, the models can stand-alone and be populated
either directly via APIs or automatically based on course naming conventions so
that any features that rely on them can work in either system.


Implementation Details
**********************

* Create a new CatalogCourse model

* A 1:N mapping between 1 Catalog Course and N Course Run objects.

  * Open question: do we re-use CourseOverview to represent Course Run, or do we make a new CourseRun run model?

* A 1:N mapping between 1 Organization and N Catalog Course objects.

* A django admin that allows you to View and Manipulate Catalog Course objects and their associations.

* A data migration to make all current implicit associations explicit.

* Eventing hooks to auto-associate new runs to their implicit Catalog Course

* A REST api to CRUD Course Overview. Catalog Course, and Org data, along with their associations.
