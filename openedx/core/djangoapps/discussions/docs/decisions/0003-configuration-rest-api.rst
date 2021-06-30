Expose Discussion Configuration via HTTP API
============================================


Status
------

Proposal


Context
-------

As part of the BD-03 initiative (Blended Development, Project 3),
we have previously created a discussion provider configuration backend,
`DiscussionsConfiguration`, as well as a new microfrontend (MFE),
`frontend-app-course-authoring`.

However, these two systems cannot yet interact with one another.

This document proposes the creation of a new HTTP API to connect the two.


Requirements
------------

For a given `context_key`, this API must allow:
- retrieval of:
  - the list of available providers
  - any options for the active provider
- creation of:
  - new configurations
- updating of:
  - existing configurations
- deletion/disabling of:
  - unneeded/inactive configurations


Consideration
-------------

The API should follow existing best-practices and technology as exists
in `edx-platform`. We should _not_ introduce new API architecture.


Decision
--------

We propose to implement this as a Django REST Framework (DRF)-based HTTP API.

This API will provide the following HTTP methods:
- GET
  - Retrieve collection of active and available providers,
    as well as their options
- POST
  - Create, update, or disable a configuration


Payload Shape
-------------

The payload is expected to be shaped like this (key names subject to change):

.. code-block:: python
    payload = {
        'context_key': str(configuration.context_key),
        'enabled': configuration.enabled,
        'features': {
            'discussion-page',
            'embedded-course-sections',
            'lti',
            'wcag-2.1',
        },
        'plugin_configuration': configuration.plugin_configuration,
        'providers': {
            'active': configuration.provider_type or '',
            'available': {
                provider: {
                    'features': AVAILABLE_PROVIDER_MAP.get(provider).get('features') or [],
                }
                for provider in configuration.available_providers
            },
        },
    }

The following configuration values are explicitly omitted;
this should be left entirely up to the MFE.
-  name
-  logo
-  description
-  support_level
-  documentation URL

The LTI configuration (keys, secrets, URLs, etc.) are considered
out-of-scope at this time.
