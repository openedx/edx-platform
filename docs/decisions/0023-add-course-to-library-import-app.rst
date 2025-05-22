Add new Django application for Modulestore to Learning Package import
=====================================================================

Status
------
Proposed

Context
-------

As part of the Library Overhaul project, a new feature is required to
handle a course content import process from the Modulestore into a
Learning Core based Learning Package preserving the Import Log.
This feature will enable users to populate Learning Package (today, that
is always Content Libraries) with existing course structures and content.
Currently, there is no mechanism to manage the Import process gradually
preserving the Import Log for a further analyze.
This creates a significant manual effort when users want to reuse existing
course content within a library.

This ADR focuses specifically on creating a new Django application
*within the `cms` service* to handle this import functionality.
The application will, initially, *only* support importing from the
local Open edX platform's Modulestore.  Support for other sources
(e.g., remote LMSs) is explicitly out of scope for this initial
implementation but is a consideration for future evolution.

The application will provide the following functionality:

*   A Python API for programmatic access to the import functionality.
*   A REST API for external interactions (e.g., from the frontend).
*   Django admin actions to initiate the import process.
*   A robust import history, enabling undo operations.
*   Integration with the `content_staging` application to manage the staging and review process.
*   Choose the level of decomposition for the import (e.g., Sections, Subsections, Units).

Problem Statement
----------------
How can we efficiently and reliably import course content from Modulestore
into Content Libraries within the `cms` service, ensuring data integrity
and providing a user-friendly workflow?

Decision
--------

Create a new Django application within the `cms` service named `import_from_modulestore`
(or a similar descriptive name) to handle the import of a modulestore-based course or
legacy library into a learning-core based learning package.

This application will be responsible for:

*   **Initiating the import:** Selecting a course (identified by course keys) from
    Modulestore to import into a specified Content Library.
*   **Staging the content:** Utilizing the `content_staging` application to
    create a temporary, editable copy of the course content.
    This allows for review and modification *before* the content is permanently added to the library.
*   **Review and Edit:**  The user will be able to review the staged
    content to ensure it meets their needs.
*   **Completing the import:** Finalizing the import process, transferring the staged
    content from `content_staging` into the target Content Library.
*   **Maintaining Import History:** Recording each import operation, including the source
    course, target library, timestamp, user, and imported blocks.
    This history will be used to support undo functionality.
*   **Handling Overwrites:**  Detecting and warning users when attempting to import content
    that already exists in the target library (based on block IDs/usage keys).
    The application should provide options to either skip the conflicting blocks, overwrite
    the existing content, or create new versions (if versioning is supported).
*   **Supported Hierarchy Levels:** Initially support importing at the Section, Subsection,
    and Unit levels.

Key Design Decisions:

*   **Dependency on `content_staging`:** Leverage the existing `content_staging` app for the
    review and editing workflow. This avoids duplicating functionality and provides a consistent
    user experience.
*   **API-Driven Design:**  Provide both Python and REST APIs to enable flexible integration
    with other parts of the system and external tools.
*   **Undo Functionality:**  The import history will be the foundation for implementing undo
    operations, allowing users to revert import actions.
*   **Modulestore as Initial Source:**  Focus on importing from the local Modulestore *only*
    for this initial implementation. This reduces complexity and allows for a faster initial release.
*   **Clear Naming:** The application and its components should have clear and descriptive
    names that reflect their purpose.

Consequences
--------

*   **New Django Application:** A new Django application (`import_from_modulestore`) will
    be added to the `cms` codebase. This increases the overall size of the `cms` service.
*   **Increased Code Complexity:**  The `cms` service will have increased complexity due to
    the new application and its interactions with `content_staging` and Modulestore.
    This requires careful design and thorough testing.
*   **Database Changes:**  New database models will likely be required to store the import history.
*   **Potential for Performance Impacts:** Importing large courses could have performance
    implications. The application should be designed to handle large imports efficiently
    (e.g., through asynchronous tasks, progress indicators).
*   **Future Extensibility:** The design should be flexible enough to accommodate future
    extensions, such as importing from different sources.
*   **Maintenance Overhead:** The new app will require ongoing maintenance.

Alternatives Considered
----------------------
* **Extending Existing Apps:** Modifying existing applications to handle the import
    functionality was considered. However, this was rejected because the import process
    has a distinct set of responsibilities and would have significantly increased
    the complexity of the existing applications. It's better to follow the principle of
    single responsibility.
* **Separate Microservice:** Creating a completely separate microservice for course import
  was considered. This was rejected for the initial implementation due to the added complexity
  of inter-service communication and deployment.  It remains a viable option for the future if
  the import functionality needs to scale independently.
