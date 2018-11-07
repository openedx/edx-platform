4. OAuth Dispatch as Router
---------------------------

Status
------

Accepted

Context
-------

Although we decided to transition from DOP to DOT and from OpenID Connect to
JWT Tokens, we are not able to update all of our clients and microservices
rapidly. In the meantime, the Mobile team wants to move forward with DOT to
support refresh tokens for the mobile apps.

Decision
--------

Start using DOT for new OAuth2 clients and newer versions of the Mobile app,
while supporting older DOP clients until all clients are updated to using
DOT.

The OAuth Dispatch app will function as a content-based router to the multiple
`OAuth2`_ provider implementations that will need to exist within the platform
during the transition phase. The app will route incoming OAuth2 REST requests
based on the value of the client_id field in the request. If the client_id
identifies an Application in DOT, then the request is routed to the DOT library.
Otherwise, the request is routed to the DOP library.

Once we fully execute the `transition plan from DOP to DOT`_, we will continue
to use and maintain this app as it will also contain edx-specific customizations
that we will add over time. At that point, the app will no longer act as a
router but will retain its proxy functionality to DOT.

.. _OAuth2: https://tools.ietf.org/html/rfc6749
.. _transition plan from DOP to DOT: https://openedx.atlassian.net/wiki/spaces/OpenDev/pages/327778541/OAuth+2.0+Roadmap

Consequences
------------

Pluses
~~~~~~

* The OAuth Dispatch app will provide an intermediary interface to the underlying
  implementation(s), which shields the rest of the platform from changes in the
  underlying libraries.

Minuses
~~~~~~~

* The LMS' security would be impacted if there are security vulnerabilities found
  in either DOP or DOT. Since DOP is no longer supported, security issues may not
  be addressed.
