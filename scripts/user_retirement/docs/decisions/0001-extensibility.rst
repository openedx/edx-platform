0001 - Retirement Extensibility
-------------------------------

Status
======

Draft -> Accepted

Context
=======

User retirement was originally built in a separate repository named Tubular, which has since been deprecated and the code moved here. Organizations running the retirement pipeline often tended to fork Tubular and maintain their custom code in their fork. This made it difficult to maintain and upgrade the retirement pipeline even before it was moved to edx-platform. The move to edx-platform has made it even more difficult to maintain custom retirement code.

In order to ensure this key piece of functionality is usable and maintainable for organizations of all sizes, we want to make it easier to extend and customize the retirement pipeline without needing to fork the codebase, and with minimal disruption to existing workflows.

Decisions
=========

#. We will use Stevedore extensions to enable adding new retirement APIs and steps to an organization's workflow without modifying the core retirement pipeline code. This will allow organizations to extend user retirement by simply installing their custom code as a Stevedore extension and changing `their configuration`_ to take advantage of the new capabilities. There should be no need to fork the edx-platform / user_retirement codebase.

#. A new `retirement_driver` entrypoint will be added to the user_retirement setup.cfg file to allow Stevedore to discover and load custom retirement extensions, which will be referred to as "drivers". An entrypoint would look like this:

   .. code-block:: python3

        [options.entry_points]
        # `retirement_driver` is the namespace chosen by our Stevedore extension manager, and where
        # the retirement pipeline will look for custom drivers if they are configured.
        retirement_driver =
            DRIVER_NAME = import.path.to.API.object:ApiObjectName
            # Examples:
            AMPLITUDE = custom_retirement.amplitude_api:AmplitudeApi
            SALESFORCE = utils.thirdparty_apis.salesforce_api:SalesforceApi


#. Custom retirement drivers will be Python classes very similar to the `utils/third_party_apis/*Api` objects that are currently used in the retirement pipeline. They will be responsible for implementing the retirement functionality that an organization wants to add.

#. Drivers must implement the following methods to be API compatible with the retirement pipeline:

   * `get_instance(config)`: This *static method* will take the entire retirement configuration dictionary and return an instance of the driver object.

   * One or more methods that are called by the retirement driver to retire a single user. Each API class can support multiple methods which can be called as different pipeline steps in the same way as the LMS class does currently. Each method must accept a single argument - a `user` dictonary containing the retirement-relevant description of a user. The method name to be called is defined in the pipeline step configuration:

    .. code-block:: python3

        - ['STEP_1', 'STEP_1_COMPLETE', 'DRIVER_NAME', 'method_name']
        - ['STEP_2', 'STEP_2_COMPLETE', 'DRIVER_NAME', 'another_method_name']
        # Example:
        - ['RETIRING_EMAIL_LISTS', 'EMAIL_LISTS_COMPLETE', 'LMS', 'retirement_retire_mailings']
        - ['RETIRING_ENROLLMENTS', 'ENROLLMENTS_COMPLETE', 'LMS', 'retirement_unenroll']

#. Any logical step than can fail (ex: API call to a service that changes state) must be a separate method. This allows the retirement pipeline to handle failures gracefully, achieve greater idempotency, and enables retrying each individual step if necessary.

#. As stated above, the entire configuration dictionary will be passed to the driver's `get_instance` method. This configuration is a dictionary version of the `configuration file`_ passed in to the retirement worker, and must contain all the configuration options that the driver needs to operate. The configuration dictionary will be passed to the driver's methods as the only argument. While scoping the configuration passed in to each driver would provide more secure isolation of secrets between drivers, it would also make it more difficult to share configuration (for instance in the case where a driver needs to access LMS or other configured service APIs as part of it's work)..

#. The existing `utils/third_party_apis/*Api` objects will be removed from edx-platform as they are highly specific to edx.org and can be trivially reimplemented as one or more custom retirement drivers.

Consequences
============

* Organizations will be able to extend the retirement pipeline without forking the codebase.
* Organizations will be able to share retirement pipeline drivers with the community.
* Organization-specific retirement steps will be removed from edx-platform.
* Organizations using the existing third-party APIs will need to reimplement them as custom retirement drivers, or find a community-supported replacement. They will also need to update their deployment and configuration to use the new driver.

Rejected Alternatives
=====================

Scoping driver configuration
----------------------------
Refactoring the retirement configuration to be more secure by scoping the configuration passed in to each driver was considered. This would provide better isolation of secrets between drivers and the default services, but would also make it more difficult to share configuration. For instance some drivers need to access LMS APIs, and doing so would require copying the LMS URL, client id, and client secret for each driver that needed them.

This seemed unnecessarily complex and more error prone than simply passing the entire configuration dictionary to each driver.

Forking the codebase
--------------------

Returning to forking the user_retirement code as the standard was considered as a way to extend the retirement pipeline, but was rejected because it would make it difficult to maintain and upgrade the retirement pipeline. It would also make it difficult to share drivers with the community.

References
==========

At the time of writing, a functioning prototype implementation of this work is available for review on this draft PR: https://github.com/openedx/edx-platform/pull/35714/files
