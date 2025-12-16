# Instructor Dashboard – Open Response Assessment (ORA) API Specification

## Status
Accepted

## Context

The Instructor Dashboard is being migrated to a Micro-Frontend (MFE) architecture, which requires stable, well-defined, and RESTful API endpoints.

The existing Open Response Assessment (ORA) functionality exposes summary and detailed assessment data through legacy endpoints that are tightly coupled to server-rendered views. These endpoints do not meet the requirements for MFE consumption, including consistent URL patterns, centralized permission handling, and standardized API documentation.

To support the migration, a new versioned ORA API is required that follows RESTful principles and aligns with existing Instructor v2 APIs.

## Decisions

### 1. RESTful Resource-Oriented Design

Introduce a versioned API under `/api/instructor/v2/` using resource-oriented URLs and clear HTTP semantics.

**Summary endpoint**

```http
GET /api/instructor/v2/courses/{course_key}/ora/summary/
```

Returns aggregated ORA statistics for a course, including:

- Total units
- Total assessments
- Total responses
- Counts by assessment type (training, peer, self, waiting, staff)
- Number of final grades received

**Detail endpoint**

```http
GET /api/instructor/v2/courses/{course_key}/ora/
```

Returns detailed ORA data, including a list of assessments with per-assessment metrics such as response counts and grading progress.

### 2. Permission-Based Tab Configuration

Server-side logic determines which Instructor Dashboard tabs are available to the current user based on their roles, course configuration, and feature flags.
Only authorized tabs are returned, each including URLs that map directly to the corresponding MFE routes.

### 3. Serializer-Based Business Logic

Use Django REST Framework serializers (`ORASSummarizerSerializer` and `ORASerializer`) to encapsulate all business logic, including:

- Data aggregation and formatting
- Permission enforcement
- Enrollment and course queries

Views remain thin and focused on request handling.

### 4. OpenAPI Specification

Maintain an OpenAPI specification at:

```
../references/instructor-v2-ora-api-spec.yaml
```

During the design phase, this specification serves as a reference and is not included in the platform-wide API documentation at `/api-docs/`.

Once implemented, the live schema exposed at `/api-docs/` is treated as the source of truth for endpoints, schemas, authentication, parameters, and error formats.

After implementation, the OpenAPI specification will be updated to match the live schema and included in `/api-docs/`.

## Consequences

- Reduced MFE page load latency by replacing multiple client requests with a small number of API calls
- Centralized business logic ensures consistent permission checks and data formatting
- Simplified client-side logic for the Instructor Dashboard MFE
- OpenAPI documentation enables type-safe client generation and easier integration

## References

- OpenAPI Specification: `../references/instructor-v2-ora-api-spec.yaml`
- Live API Documentation: `/api-docs/`
