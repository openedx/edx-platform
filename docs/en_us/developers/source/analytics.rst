.. _analytics:

##############
Analytics
##############

The edX LMS and Studio are instrumented to enable tracking of metrics and events of interest. These data can be used for educational research, decision support, and operational monitoring.

The primary mechanism for tracking events is the `Event Tracking`_ API. It should be used for the vast majority of cases.

=================
Event Tracking
=================

The `event-tracking`_ library aims to provide a simple API for tracking point-in-time events. The `event-tracking documentation`_ summarizes the features and primary use cases of the library as well as the current and future design intent.

Emitting Events
*****************

Emitting from server-side python code::

    from eventtracking import tracker
    tracker.emit('some.event.name', {'foo': 'bar'})

Emitting from client-side coffee script::

    Logger.log 'some.event.name', 'foo': 'bar'

.. note::
    The client-side API currently uses a deprecated library (the ``track`` djangoapp) instead of the event-tracking library. Eventually, event-tracking will publish a client-side API of its own: when available, that API should be used instead of the ``track``-based solution. See :ref:`deprecated_api`.

Naming Events
==============

Event names are intended to be formatted as `.` separated strings and help processing of related events. The structure is intended to be `namespace.object.action`. The namespace is intended to be a `.` separated string that helps identify the source of events and prevent events with similar or identical objects and actions from being confused with one another. The object is intended to be a noun describing the object that was acted on. The action is intended to be a past tense verb describing what happened.

Examples:

    * ``edx.course.enrollment.activated``
        * Namespace: ``edx``
        * Object: ``course.enrollment``
        * Action: ``activated``

Choosing Events to Emit
========================

Consider emitting events to capture user intent. These will typically be emitted on the client side when a user
interacts with the user interface in some way.

Consider also emitting events when models change. Most models are not append-only and it is frequently the case that an
analyst would want to see the value of a particular field at a particular moment in time. Given that many fields are
overwritten, that information is lost unless an event is emitted when the model is changed.

Sensitive Information
=====================

By default, event information is written to an unencrypted file on disk. Therefore, do not include clear text passwords, credit card numbers, or other similarly sensitive information.

Size
======

A cursory effort to regulate the size of the event is appreciated. If an event is too large, it may be omitted from the event stream. However, do not sacrifice the clarity of an event in an attempt to minimize size. It is much more important that the event is clear.

Debugging Events
=================

On devstack, emitted events are stored in the ``/edx/var/log/tracking.log`` log
file. This file can be useful for validation and debugging.

Documenting Events
*******************

The *edX Platform Developer Documentation* provides guidelines for `Contributing
to Open edX
<http://edx.readthedocs.org/projects/userdocs/en/latest/process/index.html>`_`.
As part of your effort to add events to the platform, consider including
comments that identify the purpose of the events and the fields emitted for
them. A description can assure that researchers and other members of the open
edX community understand your intent and use the event correctly.

The `edX Research Guide
<http://edx.readthedocs.org/projects/devdata/en/latest/>`_ includes reference
information for emitted events that are included in tracking logs.

Request Context Middleware
**********************************

The platform includes a middleware class that enriches all events emitted during the processing of a given request with details about the request that greatly simplify downstream processing. This is called the ``TrackMiddleware`` and can be found in ``edx-platform/common/djangoapps/track/middleware.py``.

Legacy Application Event Processor
**********************************

In order to support legacy analysis applications, the platform emits standard events using ``eventtracking.tracker.emit()``. However, it uses a custom event processor which modifies the event before saving it to ensure that the event can be parsed by legacy systems. Specifically, it replicates some information so that it is accessible in exactly the same way as it was before. This state is intended to be temporary until all existing legacy systems can be altered to use the new field locations.

=======================
Other Tracking Systems
=======================

The following tracking systems are currently used for specialized analytics. There is some redundancy with event-tracking that is undesirable. The event-tracking library could be extended to support some of these systems, allowing for a single API to be used while still transmitting data to each of these service providers. This would reduce discrepancies between the measurements made by the various systems and significantly clarify the instrumentation.

Data Dog
*****************

Data dog is used primarily for real-time operational monitoring of a running edX platform server. It supports rapid display and monitoring of various metrics within the platform such as enrollments, user creation and answers to problems.

edX platform is instrumented to send data to `data dog`_ using the standard `dogapi`_ python package. If ``lms.auth.json`` contains a ``DATADOG_API`` key whose value is a valid data dog API key, then the edX platform will transmit a variety of metrics to data dog. Running ``git grep dog_stats_api`` will give a pretty good overview of the usage of data dog to track operational metrics.

Segment.IO
*****************

A selection of events can be transmitted to segment.io in order to take advantage of a wide variety of analytics-related third party services such as Mixpanel and Chartbeat. It is enabled in the LMS if the ``SEGMENT_IO_LMS`` feature flag is enabled and the ``SEGMENT_IO_LMS_KEY`` key is set to a valid segment.io API key in the ``lms.auth.json`` file.

Google Analytics
*****************

Google analytics tracks all LMS page views. It provides several useful metrics such as common referrers and search terms that users used to find the edX web site.

.. _deprecated_api:

Deprecated APIs
*****************

The ``track`` djangoapp contains a deprecated mechanism for emitting events. Direct usage of ``server_track`` is deprecated and should be avoided in new code. Old calls to ``server_track`` should be replaced with calls to ``tracker.emit()``. The celery task-based event emission and client-side event handling do not currently have a suitable alternative approach, so they continue to be supported.

.. _event-tracking: https://github.com/edx/event-tracking
.. _event-tracking documentation: http://event-tracking.readthedocs.org/en/latest/overview.html#event-tracking
.. _data dog: http://www.datadoghq.com/
.. _dogapi: http://pydoc.datadoghq.com/en/latest/
