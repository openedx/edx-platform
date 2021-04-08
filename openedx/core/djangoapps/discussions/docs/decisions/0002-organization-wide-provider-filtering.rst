Allow organization-wide filtering of discussion providers
=========================================================


Status
------

Proposal


Context
-------

As part of the BD-03 initiative (Blended Development, Project 3),
we want to allow Organizations to filter the list of available
third-party discussion providers.

This could be due to a number of motivations, eg:
- desired experience
- support levels
- data sharing

We would, however, want to allow for manual exceptions.

This document proposes a new configuration system that allows
admins to maintain a deny-allow-list to allow filtering of discussions
providers on a per-organization basis.


Requirements
------------

Given a particular organization, we must be able to remove options
from the list of available discussions providers during configuration.


Consideration
-------------

- Django settings based (remote config, etc.)
  - pros:
    - ease of implmentation
  - cons:
    - overhead in maintenance (even with remote config, it would require
      an engineer to make a code/config change and pull request
- Database-backed
  - pros:
    - ease of use
      - by (django) admins
  - cons:
    - possible schema lock-in
      - eg: do we scope it to `organizations` only?
            or do we generalize it enough to use elsewhere?


Decision
--------

We propose to implement this as a Django database-backed model,
`ProviderFilter`.

The underlying model can be represented as:

.. code-block:: python
    class ProviderFilter(StackedConfigurationModel):
        allow = models.CharField(blank=True, ...)
        deny = models.CharField(blank=True, ...)

- `allow` is a comma-delimited string of providers to allow

- `deny` is a comma-delimited string of providers to deny

By extending the `StackedConfigurationModel`, we gain the flexibility of
stacking global/site/org/course/run values to not only provide
organization-wide filtering today, but to arbitrary levels of
granularity in the future. As this base model already exists in
`edx-platform`, integration is low-effort.


Examples
--------

With this system, we can configure global/site-wide defaults,

.. code-block:: python
    ProviderFilter.objects.create()

And then override to deny an external provider for an organization:

.. code-block:: python
    ProviderFilter.objects.create(
        org='Piazza-Less',
        deny='lti-providerx',
    )

Or override to deny _all_ external providers for an organization:

.. code-block:: python
    ProviderFilter.objects.create(
        org='InternalOrganization',
        allow='cs_comments_service',
    )

And grant an exemption to a specific course:

.. code-block:: python
    ProviderFilter.objects.create(
        # a course in 'InternalOrganization'
        course=course,
        allow='cs_comments_service lti-providerx',
    )


Logic
-----

.. code-block:: python
    _filter = get_filter(course_key)
    if _filter is None:
        allow = set()
        deny = set()
    available = defaults
    if len(allow) > 0:
        available = available.union(allow)
    if len(deny) > 0:
        available = available.difference(deny)

By default, all installed providers are available.

If no database record exists for the organization, the allow and deny
lists are considered empty, ie, there are no restrictions.

If there are any items in the allow list, all _other_ providers will be
removed from the available list.

If there are any items in the deny list, _these_ providers will be
removed from the available list.

The order of operations between the deny and allow should be
interchangeable.
