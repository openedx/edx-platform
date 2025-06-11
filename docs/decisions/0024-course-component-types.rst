Course Component Types Page
###########################

**Status**: Proposed
**Date**: 2025‑06‑02
**Target release**: Ulmo/Verawood

-----

Problem Statement
*****************

Course authors currently enable or disable XBlocks for each course via Advanced Settings → "Advanced modules" and the corresponding JSON configuration fields. This user interface is rather difficult for the average user to navigate: it ties the Studio UI to low‐level block keys that the user must locate in documentation or block code, and it does not display any block metadata (documentation, support level, etc.).

The new **Course Component Types page** (see *Figure 1*) provides a catalog-style interface where authors can browse, search, and enable blocks. To support this page, we must:

* Store canonical metadata for each installed XBlock.
* Store activation for each course.
* Safely transfer the existing configuration.
* Synchronize the functionality of the new block addition flow from the Course Component Types page and the old one through Advanced modules until it is removed.

Architectural diagrams (*Figures 2 and 3*) illustrate the interaction during execution.


Decision
********

Domain Models
=============

.. list-table:: Domain Models
   :widths: 25 35 40
   :header-rows: 1

   * - Model
     - Responsibility
     - Key Fields
   * - **ComponentType**
     - Canonical catalog record for an XBlock type. Contains fields for global overrides specified in the subtitle, description, documentation urls block.
     - ``title``, ``slug`` (entry‑point name), ``enabled`` *(global default)*, ``support_level`` *(global default)*, ``component_type`` (``common`` | ``advanced`` | ``external``, default=``advanced``), ``created``, ``updated``, ``is_experimental``, ``title`` (optional override), ``subtitle`` (optional override), ``description`` (optional override), ``documentation_url`` (optional override).
   * - **CourseComponentType**
     - Join between ``ComponentType`` and ``CourseKey`` storing per‑course enablement.
     - ``id``, ``course_key``, ``content_block``, ``enabled``, ``created``, ``updated``, ``configurable_fields`` (JSON).

Both models live in the existing app ``common.djangoapps.xblock_django``. A unique constraint ``(course_key, content_block)`` prevents duplicates.

Bootstrap and migration
=======================

* Created json with a list of default component types. (The list of component types and data about them can be viewed here_) (All other component types will be marked as experimental during migration)
* Created a migration that fills in the records in `ComponentType` according to the specified json and creates records for each course in CourseComponentType for the enabled component types.
* Created a migration/management command that scans all types of components added to the Advanced modules list and creates corresponding entries in ComponentType if a component with such a slug exists/is available in entry_points. Creates entries in CourseComponentType according to the enabled component types in courses.

.. _here: https://openedx.atlassian.net/wiki/spaces/COMM/database/4499341322


Runtime APIs
============

.. list-table:: Runtime APIs
   :widths: 30 10 60
   :header-rows: 1

   * - Endpoint
     - Method
     - Purpose
   * - ``/api/course_component_types/v1/<course_id>/``
     - GET
     - Return **all enabled component types** for a course. Supports ``?component_type=common|advanced|external`` filter.
   * - ``/api/course_component_types/v1/<course_id>/``
     - POST
     - Add a new component type to the course. The request body must contain ``slug`` (entry‑point name). If the component type is enabled globally, it will be enabled for the course. If the component type is not enabled globally, it shouldn't be added to the course.
   * - ``/xblock/<usage_key>/<view_name>`` (configurable_fields_info|metadata_info)
     - GET
     - **XBlock Info Handler** (*Fig. 3*) to return ``metadata``(``title``, ``subtitle``, ``description`` etc.) or data about ``configurable_fields`` like a field name, type, value, help etc.
   * - ``/api/course_component_types/v1/<course_id>/<slug>/``
     - POST
     - Persist author edits to component type specific configuration fields (dynamic schema) and store to ``CourseComponentType`` as JSON.


Serializers source immutable metadata from ``ComponentType``, then layer per‑course overrides from ``CourseComponentType``.

New mixin
=========

* **``StudioConfigurableXBlockMixin``** Adds and lists the configuration fields of the component. These fields are also added to the non_editable_fields of the block so that they cannot be changed from the edit form on the unit page. The list of configuration fields can be overridden in the child classes of the corresponding blocks. The mixin also adds default values for metadata fields such as title, subtitle, description, and documentation links. At the same time, it provides an interface for obtaining the values of these fields, as they can be overwritten by the administrator in BlockConfig (shown in the diagram).

Waffle Flag `...enable_course_component_types_page`
===================================================

.. list-table:: Waffle Flag ``...enable_course_component_types_page``
   :header-rows: 1

   * - Flag state
     - Behaviour
   * - **Enabled**
     - "Course Component Types" appears under *Content* menu; Course Component Types page is accessible.
   * - **Disabled**
     - Legacy behaviour intact, Course Component Types page is hidden.

Advanced Modules Field Deprecation
==================================

The "Advanced module list" field is hidden by default as an deprecated field. It is displayed after clicking the "Show deprecated settings" button and is marked as deprecated. The "Advanced module list" field still retains its full functionality but will be removed over time.


Consequences
************

* Every new installed XBlock must be added to the ``ComponentType`` table.
* When a user adds a new component type to the Advanced modules list, a corresponding entry with a link to the course is created in CourseComponentType.
* The "Course Component Types" page is discoverable and provides a better UX for course authors.
* If a component type is not enabled in the Advanced modules list, it will be hidden from the course author on the Studio unit page, and they will not be able to add it to the course, but already added this type on components will continue to work. (Same as the current behavior.)
* The new API endpoints allow for dynamic configuration of component types and retrieval of metadata.
* The new mixin allows for easy addition of configuration fields to XBlocks and provides a consistent interface for metadata.
* Many existing component types will be marked as experimental during migration, allowing for a gradual transition to the new system.
* The "Advanced module list" field is deprecated, and its functionality will be removed in the future.
* Many new DB entries will be created during the migration, but this is a one‑time cost.


Rejected Alternatives
*********************

* **Hardcoded list of common blocks**: This would not allow for extensibility or dynamic configuration. To many configuration levels, it would be difficult to maintain and extend.
* **Extend existing XBlockConfiguration model**: The current implementation of XBlockConfiguration and related models(XBlockStudioConfigurationFlag, XBlockStudioConfiguration) has complex logic and rather strange behavior (when adding a block to XBlockStudioConfiguration, all other blocks disappear on the unit page, including standard ones (html, problem, video), and there is no way to enable them separately). Also, since these are fairly old models, such a significant refactoring could cause significant problems with existing data.
* **Ability to change block metadata fields on course level**: There is no need for this level, as it is unlikely that information such as component type name, description, or documentation links will need to be changed from course to course.

References
**********

* **Figure 1** – *Course Component Types page*.

.. image:: images/course_component_types_page_design.png
    :alt: Course Component Types page

* **Figure 2** – *Course Component Types API*.

.. image:: images/course_component_types_api_diagram.png
    :alt: Course Component Types API


* **Figure 3** – *Interaction diagram of the content block’s sidebar tabs*.
.. image:: images/course_component_types_system_diagram.png
    :alt: Interaction diagram of the content block’s sidebar tabs

