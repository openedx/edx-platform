.. _edX API Authentication:

##################################
edX Enrollment API Authentication
##################################

You have two options for authentication when using the edX Enrollment API:

* `OAuth 2.0`_
* `Session Authentication`_

.. note::
  You do not need to authenticate to :ref:`get enrollment details for a course
  <Get Enrollment Details for a Course>`.

*************
OAuth 2.0
*************

The edX Enrollment API uses OAuth 2.0 for authentication.  OAuth 2.0 is an open
standard used by many systems that require secure user authentication. See the
`OAuth 2.0 Standard`_ standard for more information.

========================================
Registering with Your Open edX Instance
========================================

To use the edX Enrollment API with courses on you instance of Open edX, you
must register your application with the Open edX server. See the OAuth 2.0
specification for details.

**************************
Session Authentication
**************************

To use the edX Enrollment API, you can use session authentication in your
application. 

You must authenticate as a registred edX user.

.. include:: links.rst