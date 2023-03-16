Justifying new Django applications in the edx-platform repository
=================================================================

Status
------
Accepted

Context
-------
The Open edX platform is moving toward a more modular architecture. The goal is to transition from a monolithic application in edx-platform to one in which this repository represents a small, stable core with volatility pushed into extensions and plugins. To that end, much of the original edx-platform repository has been split out into micro-frontends, other microservices, plugins, and libraries. However, there are still a number of optional and non-core Django applications within edx-platform and new ones continue to be added.
For more information on plugins in particular, see the `Django Apps Plugin README`_.

There is guidance on creating new applications in general in `OEP-49`_. This ADR should be taken as an extension of that OEP with particular guidance for adding new apps in the edx-platform repository itself.

.. _OEP-49: https://open-edx-proposals.readthedocs.io/en/latest/best-practices/oep-0049-django-app-patterns.html

.. _Django Apps Plugin README: https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins/README.rst


Decision
--------
From the adoption of this ADR, when adding a new app to the edx-platform repository, the accompanying ADR (as required in `this section of OEP-49`_) must include a justification for why this application cannot or should not be created in a different repository.

.. _this section of OEP-49: https://open-edx-proposals.readthedocs.io/en/latest/best-practices/oep-0049-django-app-patterns.html#docs-decisions-0001-purpose-of-this-app-rst

Further Guidance
----------------

While the preference should always be to develop outside the edx-platform repository, either by extending an existing external Django application repository or creating a new one, there are still acceptable reasons why a new application would be better developed within edx-platform:

* The application relates directly to core functionality: course authoring, course administration, or learner-courseware interactions
* The application requires multiple imports from edx-platform

  * Note: There are strategies for plugging apps into core LMS and CMS behaviors without directly importing edx-platform code, notably the `Hooks Extension Framework`_.
  * If it is truly necessary to import from edx-platform code directly, in addition to noting this in the ADR, the authors of the new application should add the libraries or applications it imports to the `Libraries we KNOW we want to move out of the monolith`_ Confluence page.


.. _Hooks Extension Framework: https://open-edx-proposals.readthedocs.io/en/latest/architectural-decisions/oep-0050-hooks-extension-framework.html

.. _Libraries we KNOW we want to move out of the monolith: https://openedx.atlassian.net/wiki/spaces/AC/pages/525172740/Libraries+we+KNOW+we+want+to+move+out+of+the+monolith
