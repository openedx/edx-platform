**************
Cognitive Load
**************

This is a checklist of all of the things that we expect a developer to consider
as they are building new or modifying existing functionality.

Operational Impact
==================

* Are there new points in the system that require operational monitoring?

    * External system that you now depend on (Mathworks, SoftwareSecure,
      CyberSource, etc...)
    * New reliance on disk space?
    * New stand process (workers? elastic search?) that need to always be available?
    * A new queue that needs to be monitored for dequeueing
    * Bulk Email --> Amazon SES, Inbound queues, etc...
    * Are important feature metrics sent to datadog and is there a
      dashboard to monitor them?

* Am I building a feature that will have impact to the performance of the system?

    * Deep Search
    * Grade Downloads

* Are reasonable log messages being written out for debugging purposes?
* Will this new feature easily startup in the Vagrant image?
* Do we have documentation for how to startup this feature if it has any
  new startup requirements?
* Are there any special directories/file system permissions that need to be set?
* Will this have any impact to the CDN related technologies?
* Are we pushing any extra manual burden on the Operations team to have to
  provision anything new when new courses launch? when new schools start? etc....
* Has the feature been tested using a production configuration with vagrant?

See also: :doc:`deploy-new-service`

Documentation/Training/Support
==============================

* Is there appropriate documentation in the context of the product for
  this feature? If not, how can we get it to folks?

  * For Studio much of the documentation is in the product.

* Is this feature big enough that we need to have a session with stake holders
  to introduce this feature BEFORE we release it? (PMs, Support, etc...)

  * Paid Certificates

* Do I have to give some more information to the Escalation Team
  so that this can be supported?
* Did you add an entry to CHANGELOG?
* Did you write/edit docstrings for all of your modules, classes, and functions?

Development
===========

* Did you consider a reasonable upgrade path?
* Is this a feature that we need to slowly roll out to different audiences?

  * Bulk Email

* Have you considered exposing an appropriate amount of configuration options
  in case something happens?
* Have you considered a simple way to "disable" this feature if something is broken?

  * Centralized Logging

* Will this feature require any security provisioning?

  * Which roles use this feature? Does it make sense to ensure that only those
    roles can see this feature?
  * Assets in the Studio Library

* Did you ensure that any new libraries are added to appropriate provisioning
  scripts and have been checked by OSCM for license appropriateness?
* Is there an open source alternative?
* Are we locked down to any proprietary technologies? (AWS, ...)
* Did you consider making APIs so that others can change the implementation if applicable?
* Did you consider Internationalization (I18N) and Localization (L10N)?
* Did you consider Accessibility (A11y)?
* Will your code work properly in workers?
* Have you considered the large-scale modularity of the code? For example,
  xmodule and xblock should not use Django features directly.

Testing
=======

* Did you make sure that you tried boundary conditions?
* Did you try unicode input/data?

  * The name of the person in paid certifactes
  * The name of the person in bulk email
  * The body of the text in bulk email
  * etc

* Did you try funny characters in the input/data? (~!@#$%^&*()';/.,<>, etc...)
* Have you done performance testing on this feature? Do you know how much
  performance is good enough?
* Did you ensure that your functionality works across all supported browsers?
* Do you have the right hooks in your HTML to ensure that the views are automatable?
* Are you ready if this feature has 10x the expected usage?
* What happens if an external service does not respond or responds with
  a significant delay?
* What are possible failure modes?  Do your unit tests exercise these code paths?
* Does this change affect templates and/or JavaScript?  If so, are there
  Selenium tests for the affected page(s)?  Have you tested the affected
  page(s) in a sandbox?

Analytics
=========

* Are learning analytics events being recorded in an appropriate way?

  * Do your events use a descriptive and uniquely enough event type and
    namespace?
  * Did you ensure that you capture enough information for the researchers
    to benefit from this event information?
  * Is it possible to reconstruct the state of your module from the history
    of its events?
  * Has this new event been documented  so that folks downstream know how
    to interpret it?
  * Are you increasing the amount of logging in any major way?

* Are you sending appropriate/enough information to MixPanel,
  Google Analytics, Segment IO?

Collaboration
=============
* Are there are other teams that would benefit from knowing about this feature?

  * Forums/LMS - email

* Does this feature require a special broadcast to external teams as well?
  (Stanford, Google, Berkley, etc...)

Open Source
===========
* Can we get help from the community on this feature?
* Does the community know enough about this?

UX/Design/Front End Development
===============================
* Did you make sure that the feature is going to pass
  Accessibility requirements (still TBD)?
* Did you make sure any system/instructional text is I18N ready?
* Did you ensure that basic functionality works across all supported browsers?
* Did you plan for the feature's UI to degrade gracefully (or be
  progressively enhanced) based on browser capability?
* Did you review the page/view under all browser/agent conditions -
  viewport sizes, images off, css off?
* Did you write any HTML with ideal page/view semantics in mind?
* When writing HTML, did you adhere to standards/conventions around class/id names?
* When writing Sass, did you follow OOCSS/SMACSS philosophy ([1]_, [2]_, [3]_),
  variable/extend organization and naming conventions, and UI abstraction conventions?
* When writing Sass, did you document any new variables,
  extend-based classes, or mixins?
* When writing/adding JavaScript, did you consider the asset pipeline
  and page load timeline?
* When writing JavaScript, did you note what code is for prototyping vs. production?
* When adding new templates, views, assets (Sass, images, plugins/libraries),
  did you follow existing naming and file architecture conventions?
* When adding new templates, views, assets (Sass, images, plugins/libraries),
  did you add any needed documentation?
* Did you use templates and good Sass architecture to keep DRY?
* Did we document any aspects about the feature (flow, purpose, intent)
  that we or other teams will need to know going forward?

.. [1] http://smacss.com/
.. [2] http://thesassway.com/intermediate/avoid-nested-selectors-for-more-modular-css
.. [3] http://ianstormtaylor.com/oocss-plus-sass-is-the-best-way-to-css/

edX.org Specific
================

* Ensure that you have not broken import/export?
* Ensure that you have not broken video player? (Lyla video)
