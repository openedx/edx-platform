.. _Enabling User Retirement:

####################################
Enabling the User Retirement Feature
####################################

There have been many changes to privacy laws (for example, GDPR or the 
European Union General Data Protection Regulation) intended to change the way 
that businesses think about and handle Personally Identifiable Information 
(PII). 

As a step toward enabling Open edX to support some of the key updates in privacy
laws, edX has implemented APIs and tooling that enable Open edX instances to
retire registered users. When you implement this user retirement feature, your
Open edX instance can automatically erase PII for a given user from systems that
are internal to Open edX (for example, the LMS, forums, credentials, and other
independently deployable applications (IDAs)), as well as external systems, such
as third-party marketing services.

This section is intended not only for instructing Open edX admins to perform
the basic setup, but also to offer some insight into the implementation of the
user retirement feature in order to help the Open edX community build
additional APIs and states that meet their special needs. Custom code,
plugins, packages, or XBlocks in your Open edX instance might store PII, but
this feature will not magically find and clean up that PII. You may need to 
create your own custom code to include PII that is not covered by the user
retirement feature.

.. toctree::
   :maxdepth: 1

   implementation_overview
   service_setup
   driver_setup
   special_cases

.. include:: ../../../../links/links.rst

