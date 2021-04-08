Discussion provider configuration
=================================


Status
------

Proposal


Context
-------

As part of the BD-03 initiative (Blended Development, Project 3),
we want to enable third-party discussion providers to replace the
default forums experience in edx-platform.

To accomplish this, we should establish a configuration system to
enable/disable/configure these new discussion-provider plugins;
the existing forums experience will be included as one of these plugins.

This ADR proposes a new configuration system that allows operators to create
pre-populated configurations for specific discussions providers,
which can then be used and customized by course authors/admins.


Decision
--------

We propose to implement this as a Django database-backed model with
historical records, `DiscussionsConfiguration`.

The underlying model can be represented as:

.. code-block:: python
    class DiscussionsConfiguration:
        context_key = LearningContextKeyField(primary_key=True, ...)
        enabled = models.BooleanField(default=True, ...)
        lti_configuration = models.ForeignKey(LtiConfiguration, blank=True, ...)
        plugin_configuration = JSONField(default={}, ...)
        provider_type = models.CharField(blank=False, ...)
        history = HistoricalRecords()

- Discussions can be disabled on a course by setting `enabled=False`; if
  no record exists, the plugin is considered to be disabled by default.

- `lti_configuration` is a collection of LTI launch configuration data
  (URL, key, secret, etc.), but this data structure should be extracted
  into its own model; see notes below (`Dependent Work`).

- `plugin_configuration` is a free-form dictionary of configuration
  values, to be passed to plugin's renderer

- `provider_type` is the (arbitrary, but stable) id for the discussion provider.

- `history` is tracked using Django Simple History.


Future Work
-----------

- `LtiConfiguration` should be extended for feature-parity with_out_
  XBlock dependencies.

- Discussion apps/plugins/providers, implemented as Python models, will
  be available via some discovery mechanism (Python entry points?,
  hard-coded list?)
  They will be responsible for:
  - the provider_type, referenced by `DiscussionsConfiguration`
  - any relevant renderers, accessors, etc.

- No site/organization-based provider restrictions will be implemented, at this time.
  This could be added later via an allow/deny-list.
