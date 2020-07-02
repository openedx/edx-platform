Programs Cache in LMS
_____________________

Status
======
Accepted

Decision
=========
1. Developers working on code involving programs (which is not limited Programs theme developers) should be directed to this ADR for context on the usage and limitations of the programs cache.

2. Consumers of the programs cache should expect cache misses and either handle them gracefully when possible or explicitly fail (with logging).

   a. Depending on the cache access pattern, it may be impossible to distinguish between a non-existent program and an existent program that is missing from the cache.
3. Introduce logging to the programs cache, especially in the case of cache misses or an empty cache. This will make debugging easier and make it more apparent when intervention (such as manually running cache_programs) is necessary.

4. All edX.org developers should be given access to the Jenkins job that runs cache_programs.

Context
=======
The LMS in edx-platform has a limited understanding of the structure and content of programs, as they are stored authoritatively in the Discovery service's SQL database. However, certain features of the LMS, such as displaying a learner’s programs on their dashboard, require access to the programs’ data. To fulfill this need, the LMS has the JSON responses from Discovery’s /api/v1/programs endpoint stored in memcached. The LMS uses the cache to understand what program or programs a course (run) is in. The contents of the cache are exposed through the ``openedx.core.djangoapps.catalog`` app. This system is what we are referring to when we say "the programs cache” or simply “the cache”.

This cache is populated by calling LMS’s cache_programs management command.
The cache is regularly refreshed via an external process.
By design, the cache does not populate itself by calling out to the Discovery API upon a cache miss.

Below is a (not-necessarily-exhaustive) list of features that depend on the programs cache:

* The learner dashboard shows “Related Programs” under the cards of courses that are in programs.
* The programs progress page.
* The creation of external IDs for users enrolled in courses within MicroBachelors programs requires knowledge of programs.
* The program_enrollments system, which Masters uses for institution-managed enrollments in degree programs, uses the programs cache for validation of when creating associations between program enrollments and course enrollments.
* The LMS management commands that populate program credentials need knowledge of programs.
* Temporary Experiments often utilize the programs cache.
* Courseware will reference programs information in order to show in-course recommendations.

Issues
======
Correctness & Resiliency
------------------------

Because the cache is held in volatile memory, any crash or restart of the memcache server holding the programs cache can surface these issues. While the cache_programs command can be run immediately afterwards, this is not a foolproof solution:

* For a large course catalog, this command takes time to run, so there will be at least some time where LMS programs features are broken due to missing data.
* Site operators may not know that this has to be done. Even if they do, it adds operational complexity.
* The command may fail.

Recently, the edX.org memcached cluster was restarted due to an increased LMS load. Following the restart, the cache_programs was not run immediately. As a result, there may have been an impact on LMS functionality due to the empty cache.

Developer & operator experience
-------------------------------

Requiring the regularly-scheduled execution of a management command to make the LMS fully functional adds operational complexity to courses.edx.org, Open edX instances, Devstack, and Sandboxes.

Knowledge & access
------------------
The requirements to populate the cache via the edx.org Jenkins job, the privileges required or the fact that the cache is not auto refreshed are not well known.

Future Recommendations and Alternatives
=========================================
* Call into Discovery service if cache miss happens.
   * Pros:
      * Removes the issues that arise when a program is not present in the cache.
      * Handles the case of a completely empty cache.
   * Cons:
      * Increases the dependence of LMS on Discovery.
      * Increases the potential load on the Discovery API.
      * Involves some engineering effort.
* Persist Discovery data in LMS MySQL database.
   * Pros:
      * Moving to persistent storage would mitigate the “cache accidentally emptied” issue that is inherent to volatile storage.

   * Cons:
      * Data duplication.
      * Ensuring that data is synchronized between the two caches.
      * Managing an additional SQL schema.
      * Involves significant engineering effort.
* Remove logic from LMS that relies on programs.
      * Pros:
         * Potentially best long-term solution as it reduces the amount of data/complexity.
         * All programs cache issues are de facto resolved.
      * Cons:
         * Involves potentially huge engineering and product effort to accomplish, as many features would have to be replicated elsewhere or removed.
