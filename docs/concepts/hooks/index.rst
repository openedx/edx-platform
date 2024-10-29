Hooks Extension Framework
=========================

What is the Hooks Extension Framework?
---------------------------------------

Based on the `open-closed principle`_, this framework aims to extend the platform in a maintainable way without modifying its core. The main goal is to leverage the existing extension capabilities provided by the plugin architecture, allowing developers to implement new features to fit customer needs while reducing the need for core modifications and minimizing maintenance efforts.

Hooks are a list of places in the Open edX platform where externally defined functions can take place. These functions may alter what the user sees or experiences on the platform, while in other cases, they are purely informative. All hooks are designed to be extended through Open edX plugins and configurations.

Hooks can be of two types: events and filters. Events are signals sent in specific places whose receivers can extend functionality, while filters are functions that can modify the application's behavior.

To allow extension developers to use the framework's definitions in their implementations, both kinds of hooks are defined in lightweight external libraries:

* `openedx-filters`_
* `openedx-events`_

The main goal of the framework is that developers can use it to change the platform's functionality as needed and still migrate to newer Open edX releases with little to no development effort. So, the framework is designed with stability in mind, meaning it is versioned and backward compatible as much as possible.

A longer description of the framework and its history can be found in `OEP 50`_.

.. _OEP 50: https://open-edx-proposals.readthedocs.io/en/latest/oep-0050-hooks-extension-framework.html
.. _openedx-filters: https://github.com/eduNEXT/openedx-filters
.. _openedx-events: https://github.com/eduNEXT/openedx-events
.. _open-closed principle: https://docs.openedx.org/projects/edx-platform/en/open-release-quince.master/concepts/extension_points.html

Why adopt the Hooks Extension Framework?
----------------------------------------

#. Stable and Maintainable Extensions

The Hooks Extension Framework allows developers to extend the platform's functionality in a stable, maintainable, and decoupled way ensuring easier upgrades and long-term stability by removing the need to modify the core in an significant way.

#. Contained Solution Implementation

By avoiding core modifications, the framework promotes self-contained solutions, eliminating the need  for custom code to coexist with core logic which lowers maintenance costs for extension developers.

#. Leveraging the Open edX Plugin Extension Mechanism

The framework allows developers to implement custom business logic and integrations directly in plugins. This keeps core modifications minimal, focusing maintenance and development efforts on plugins, where solutions can be built and maintained independently of the core platform.

#. Standardization

Both filters and events implementations implement an approach for adding additional features, such as communication between components or services, or backend flow control. With these standards in place, it’s easy to identify when and how to use the framework as a solution, ensuring a consistent and predictable approach to extending the platform.

#. Reduce Fork Modifications

The need to modify logic in forks is minimized, as most extensions can now be implementing using the framework, keeping forks closer to the core and easier to manage.

#. Community Compatibility

The framework allows for shorter and more agile contribution cycles. By adding standardized extension points, contributors avoid creating customer-specific logic, making development more community-friendly.

#. Backward Compatibility

Hooks are designed to be backward compatible, guaranteeing stability across releases and making it easier to upgrade without breaking existing functionality.


Open edX Events and Filters
============================

Open edX Events
---------------

Events are Open edX-specific Django signals sent in specific places on the Open edX platform. They allow developers to listen to these signals and perform additional processing based on the event data.

To start using Open edX Events in your project, see the `Open edX Events`_ documentation.

.. _Open edX Events: https://docs.openedx.org/projects/openedx-events/en/latest/

Open edX Filters
----------------

Filters are functions that can modify the application's behavior by altering input data or halting execution based on specific conditions. They allow developers to implement application flow control based on their business logic or requirements without directly modifying the application code.

To start using Open edX Filters in your project, see the `Open edX Filters`_ documentation.

.. _Open edX Filters: https://docs.openedx.org/projects/openedx-filters/en/latest/

Differences between Events and Filters
--------------------------------------

Here are some key differences between Open edX Events and Filters:

+--------------------+------------------------------------------------------------------------+-------------------------------------------------------------+
|                    | Events                                                                 | Filters                                                     |
+====================+========================================================================+=============================================================+
| **Purpose**        | Notify when an action occurs in a specific part of the                 | Alter the application flow control.                         |
|                    | application.                                                           |                                                             |
+--------------------+------------------------------------------------------------------------+-------------------------------------------------------------+
|  **Usage**         | Used to **extend** functionality via signal handlers when an event is  |  Used to intercept and **modify** the data used within a    |
|                    | triggered.                                                             |  component without directly modifying the application       |
|                    |                                                                        |  itself.                                                    |
+--------------------+------------------------------------------------------------------------+-------------------------------------------------------------+
|  **Definition**    |  Defined using the `OpenEdxPublicSignal` class, which                  |  Defined using the ``OpenEdxPublicFilter`` class,           |
|                    |  provides a structured way to define the data and                      |  which provides a way to define the filter function         |
|                    |  metadata associated with the event.                                   |  and the parameters it should receive.                      |
+--------------------+------------------------------------------------------------------------+-------------------------------------------------------------+
| **Implementation** |  Implemented using Django signals, which allow                         |  Implemented using an accumulative pipeline mechanism which |
|                    |  developers to send and receive notifications that an action happened  |  takes a set of arguments and returns a modified set        |
|                    |  within a Django application.                                          |  to the caller or raises exceptions during                  |
|                    |                                                                        |  processing.                                                |
+--------------------+------------------------------------------------------------------------+-------------------------------------------------------------+
| **Use cases**      |  Send an email notification when a user enrolls in a course.           |  Include additional information in an API endpoint response.|
|                    |  an email notification.                                                |                                                             |
+--------------------+------------------------------------------------------------------------+-------------------------------------------------------------+

How to know when to use an Event or a Filter?
----------------------------------------------

When to use an Open edX Event?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use an Open edX Event when you need to:

- Trigger custom logic or processing in response to specific actions within the platform, e.g., updating a search index after a course block is modified.
- Communicate, synchronize, or coordinate with other components or services based on specific events or actions, e.g., send certificate data from LMS to credentials service to keep models up to date.
- Integrate with external systems or services based on specific events or actions within the platform, e.g., send user data to third-party services upon registration for marketing purposes.

In summary, events can be used to integrate application components with each other or with external services, allowing them to communicate, synchronize, and perform additional actions when specific triggers occur.

You can review the `Open edX Events`_ documentation for more information on `how to use events`_ in your project. This documentation includes a `list of available events`_ and `how to implement event handlers`_.

.. _Open edX Events: https://docs.openedx.org/projects/openedx-events/en/latest/
.. _how to use events: https://docs.openedx.org/projects/openedx-events/en/latest/how-tos/using-events.html
.. _list of available events: https://docs.openedx.org/projects/openedx-events/en/latest/reference/events.html
.. _how to implement custom event handlers: https://docs.openedx.org/projects/openedx-events/en/latest/how-tos/using-events.html#receiving-events

When to use an Open edX Filter?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use an Open edX Filter when:

- Enrich the data or parameters passed to a specific component, e.g., fetch reusable LTI configurations from external plugins.
- Intercept and modify the input of a specific component, e.g., include "Edit" link to an HTML block if certain conditions are met.
- Enforce specific constraints or business rules on the input or output of a specific function or method, e.g., prevent enrollment for non-authorized users.

In summary, filters can be used when implementing application flow control that modifies the application's behavior, navigation, or user interaction flow during runtime.

You can review the `Open edX Filters`_ documentation for more information on `how to use filters`_ in your project or `create new`_. This documentation includes a `list of available filters`_ and `how to implement filters`_.

.. _Open edX Filters: https://docs.openedx.org/projects/openedx-filters/en/latest/
.. _how to use filters: https://docs.openedx.org/projects/openedx-filters/en/latest/how-tos/using-filters.html
.. _list of available filters: https://docs.openedx.org/projects/openedx-filters/en/latest/reference/filters.html
.. _how to implement filters: https://docs.openedx.org/projects/openedx-filters/en/latest/how-tos/using-filters.html#implement-pipeline-steps
.. _create new: https://docs.openedx.org/projects/openedx-filters/en/latest/how-tos/create-new-filters.html
