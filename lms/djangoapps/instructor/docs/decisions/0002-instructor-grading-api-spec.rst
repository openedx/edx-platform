Instructor Grading API Specification
-------------------------------------

Status
======

Proposed

Context
=======

The instructor dashboard provides grading operations (reset attempts, rescore, override scores,
delete state) through legacy endpoints with inconsistent patterns. These operations need to
support both single-learner (synchronous) and all-learners (asynchronous) execution models.

We needed a modern, RESTful API with consistent URL patterns, clear synchronous vs asynchronous
behavior, comprehensive task monitoring, and proper documentation.

Decisions
=========

#. **RESTful Resource-Oriented Design**

   Use resource-oriented URLs: ``/api/instructor/v2/courses/{course_key}/{problem}/grading/{resource}``

   Use appropriate HTTP methods:

   * ``GET`` for read operations (learner info, problem metadata, task status)
   * ``POST`` for actions (reset attempts, rescore)
   * ``PUT`` for replacements (score overrides)
   * ``DELETE`` for removals (delete learner state)

#. **Synchronous vs Asynchronous Execution**

   * Operations targeting a single learner (with ``learner`` parameter) execute synchronously
     and return ``200 OK`` with immediate results (< 5s typical)
   * Operations targeting all learners (no ``learner`` parameter) queue a background task
     and return ``202 Accepted`` with task tracking information
   * Provide task status endpoint: ``GET /api/instructor/v2/courses/{course_key}/tasks/{task_id}``

#. **Clear Operation Semantics**

   * **Reset Attempts**: Resets counter to zero, preserves answers/state
   * **Delete State**: Permanently removes all learner data (requires ``learner`` parameter)
   * **Rescore**: Re-evaluates submissions with current grading logic (supports ``only_if_higher``)
   * **Override Score**: Manually sets specific score (requires ``learner`` parameter)

#. **Consistent Response Formats**

   * Synchronous operations return ``SyncOperationResult`` with success, learner, problem_location, message
   * Asynchronous operations return ``AsyncOperationResult`` with task_id, status_url, scope
   * Task status responses include task_id, state, progress, result/error, timestamps

#. **OpenAPI Specification**

   Maintain a complete OpenAPI 3.0.3 specification at
   ``../references/instructor-grading-api-spec.yaml`` as the source of truth for
   endpoints, schemas, authentication, parameters, and error formats.

Consequences
============

Positive
~~~~~~~~

* Consistent URL patterns and response formats make the API predictable
* Explicit sync/async behavior allows proper UI feedback
* OpenAPI specification enables automated validation, testing, and type-safe client generation
* Resource-oriented design makes it easy to add new operations

Negative
~~~~~~~~

* Existing clients using legacy endpoints need to be updated
* Dual maintenance during transition period
* Developers familiar with legacy endpoints need to learn new patterns

References
==========

* OpenAPI Specification: ``../references/instructor-grading-api-spec.yaml``
