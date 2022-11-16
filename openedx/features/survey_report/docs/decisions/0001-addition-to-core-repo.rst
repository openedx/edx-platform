Addition of the Survey Report App to edx-platform
=================================================

Status
------
Accepted

Context
-------
The transition to a more modular architecture for edx-platorm has been
strengthened by the acceptance of the `No new Django apps ADR`_.

.. _No new Django apps ADR: https://github.com/openedx/edx-platform/tree/master/docs/decisions/0014-no-new-apps.rst


Rationale
---------

This feature was considered for inclusion into the edx-platform code because it
imports several models from the inner workings of the core functionality in
order to query them. This goes in accordance with the section further guidance
of the ADR.


Decision
--------

Locate the Survey Report Application in the edx-platform repository under
`openedx/features`.
