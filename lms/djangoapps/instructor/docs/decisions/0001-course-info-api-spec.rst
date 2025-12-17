Instructor Course Information API Specification
-----------------------------------------------

Status
======

**Accepted** *2025-10-30*

Context
=======

The instructor dashboard requires comprehensive course metadata, enrollment statistics, user
permissions, and navigation configuration. This information was previously scattered across
multiple endpoints, requiring multiple round-trip requests and complex client-side data
aggregation for MFEs.

Decisions
=========

#. **Consolidated Course Metadata Endpoint**

   Create ``GET /api/instructor/v2/courses/{course_id}`` that returns comprehensive course
   information in a single request, including course identity, timing, enrollment statistics,
   user permissions, dashboard tab configuration, and operational information.

#. **Permission-Based Tab Configuration**

   Server-side logic determines which dashboard tabs the current user can access based on
   their roles, course features, and system configuration. Tabs are returned with URLs
   pointing to the appropriate MFE routes.

#. **Serializer-Based Business Logic**

   Use Django REST Framework serializers (``CourseInformationSerializer``) to encapsulate
   all business logic for data gathering, permission checks, enrollment queries, and
   formatting. Keep views thin.

#. **OpenAPI Specification**

   Maintain an OpenAPI specification at ``../references/instructor-v2-course-info-spec.yaml`` to guide implementation. This static specification serves as a reference during development, but ``/api-docs/`` is the source of truth for what is actually deployed. Once implementation is complete and the endpoints are live in ``/api-docs/``, the static spec file will be deleted to avoid maintaining outdated documentation.

Consequences
============

Positive
~~~~~~~~

* Single request replaces multiple round-trips, reducing latency for MFE page loads
* Centralized business logic ensures consistent permission checks and data formatting
* Simplified client code with all course information available in one call
* OpenAPI specification enables type-safe client generation

Negative
~~~~~~~~

* Larger response payload (though offset by eliminating multiple requests)
* Some over-fetching when clients don't need all information
* Permission-based data prevents simple course-level caching
* Enrollment queries and permission checks run on every request

References
==========

* OpenAPI Specification: ``../references/instructor-v2-course-info-spec.yaml``
* Implementation: ``lms/djangoapps/instructor/views/api_v2.py``
* Live API Documentation: ``/api-docs/``
