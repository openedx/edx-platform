Record External ID Table Decision
=================================

Status
------

Accepted

Context
-------

Third Parties at times require a unique user ID as part of the data that they can
access about a Learner. We would like to avoid sending them internal IDs
to protect our internal data models.

We also have Hash IDs that are used for some reporting and other external sources as
part of the anonymous ID table.  The use case of the anonymous ID table is to provide
anonymous user identifiers. The External ids will be shared with identifiable
information and are therefore not anonymous.

ExternalIdType defines the type (purpose, or expected use) of an external id. A
user may have one id that is sent to Company A and another that is sent to Company B.

External ids are sent to systems or companies outside of Open edX. This allows us
to limit the exposure of any given id.

An external id is linked to an internal id, so that users may be re-identified if the external id is sent
back to Open edX.

Decisions
---------

- External ids will be UUIDs.
- Users will only have exactly 1 external id per ExternalIDType.
- All Types will have a clear description in the ExternalIDType table so that we can later determine why this type was created. If the type was created to send to Company A, the description can help determine if ids of this type may also be sent to Company B
- All ExternalIDTypes should be easily referenced in the platform to support getting User information based on External ids.
- We will add an External id table to support different types of generated UUIDs.

Consequences
------------

We will have a clear unique ID to share with external entities that can reference
an internal User. All external entities should have their own type so that Users
can have multiple External ids, 1 per type.

References
----------

Model definition
- https://github.com/edx/edx-platform/blob/a5ec801a2a91f928bf582ee9ba2092a5bfbe7d7e/openedx/core/djangoapps/external_user_ids/models.py#L17

Anonymous User ID Table
- https://github.com/edx/edx-platform/blob/6ee2089077b76581e14f230f0c9224757dbdb652/common/djangoapps/student/models.py#L130-L140

Some notes on why add a type table
- https://www.itprotoday.com/sql-server/trouble-type-tables
