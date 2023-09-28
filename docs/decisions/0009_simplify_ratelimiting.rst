Simplify Login and Other Rate Limiting
======================================

Status
------

Accepted

Decisions
---------

* We will deprecate and remove the `django-ratelimit-backend`_ from
  edx-platform. This library is currently not being actively developed and is
  looking for a new maintainer.  It is also very specific to rate limiting the
  authentication backend and so can't easily be applied more generally.

* For rate limiting in pure django views, we will use the `django-ratelimit`_
  library. This library is well built for general use and can be easily used
  multiple times for stacked rate limiting over multiple keys.  eg. limit by IP
  or by user name.

* For rate limiting in any DRF based views, we will use the
  `djangorestframework rate limiting`_ capabilities that are built in to the
  framework.


Context
-------

edx-platform currently uses multiple different ratelimiting tools which can
lead to confusion and difficulty understanding how endpoints are secured.
Consider the following case study in how our login endpoints are currently rate
limitied.

Rate limiting Logins
~~~~~~~~~~~~~~~~~~~~

1st party vs 3rd party login
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

edx-platform allows for both 1st party auth, where you provide the LMS with
your credentials and it gives you back some session tokens, and also 3rd party
auth, in which you are directed to a 3rd party to authenticate and then
redirected to the LMS with a token from that third party which is exchanged for
1st party(LMS) session tokens.

Login User View
^^^^^^^^^^^^^^^

The ``login_user`` view in ``views/login.py`` is called for both 1st and 3rd
party login flows.  In the 3rd party login flow, it's called as the callback
when redirected from the 3rd party login back to the LMS.

Currently this view is accessed through two different endpoints.  It is
currently a pass-through call for the ``/api/user/v1/account/login_session``
using a DRF view.  It is also called directly at ``/login_ajax``

Currently there are five different rate limiting implementations in use as a
part of the login flow.

* `django-ratelimit`_ - A 3rd party rate limiting library that allows you to
  decorate any view to add rate limiting functionality.

  The ``ratelimit`` decorator on ``login_user`` uses the
  LOGISTRATION_RATELIMIT_RATE django setting to determine the rate limit.  The
  default is ``100 requests per 5 minutes``  This applies to both 1st and 3rd
  party login attempts.

* `django-ratelimit-backend`_ - Another 3rd party rate limiting library built
  specifically to rate limit login views.  It provides a mixin that we can add
  to an existing auth backend.  This replaces the base implementation of the
  ``authenticate`` class with one that will also track the rate limits for that
  call.

  We currently use the default rate limits provided by the upstream library
  which is ``30 requests per 5 minute``  This is only applies to 1st party
  login attempts and does not count against 3rd party logins.

* `djangorestframework rate limiting`_ - DRF provides a throttling
  capability that can be used with any DRF views.  This is not used for the
  login view but is applied to the ``/third_party_auth_context`` endpoint
  (``TPAContextView``) to rate limit 3rd party auth requests.  The default
  rate limit for this endpoint is ``20 requests per minute``.  Since this rate
  limiting is only applied to a 3rd party auth specific view, it only impact
  the rate at which 3rd party auth is possible.

* `MAX_FAILED_LOGIN_ATTEMPTS`_ - This is an optional feature that can be
  enable(disabled by default) which will limit the number of failed logins a
  user is allowed to have before their account is locked out.  This feature
  works slightly differently from the other rate limiting features in that it
  persists the number of failures and does not reset them until we have had a
  successful login.  If a maximum number of failed request is reached, the
  account is locked out for 30 minutes.  The default settings for this feature
  are to lock out the user for 30 minutes if 6 login failures occur over any
  period of time.

  edx.org has the ``MAX_FAILED_LOGIN_ATTEMPTS`` feature enabled.

* `cloudflare rate limiting`_ - This is edx.org specific and not enabled by
  default for Open edX.

Ratelimiting other endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Other endpoints usually use only one of the above mentioned 3 libraries(drf,
django-ratelimit, django-ratelimit-backend).  The decision below should clarify
how and when we should be using different libraries.


.. _django-ratelimit: https://django-ratelimit.readthedocs.io/en/stable/usage.html#usage-chapter
.. _django-ratelimit-backend: https://django-ratelimit-backend.readthedocs.io/en/latest/
.. _djangorestframework rate limiting: https://www.django-rest-framework.org/api-guide/throttling/
.. _MAX_FAILED_LOGIN_ATTEMPTS: https://github.com/openedx/edx-platform/blob/cd6064692681ab99912e3da3721cd857a0b313e9/common/djangoapps/student/models.py#L980
.. _cloudflare rate limiting: https://www.cloudflare.com/rate-limiting/
