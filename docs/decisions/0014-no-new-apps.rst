14. Documentation of new apps in edx-platform

Status
------
In Review

Context
-------
In recent years, edX and the software industry as a whole have been moving away from a monolith structure towards more modular architecture. The goal is to transition from a base site with plugins to a collection of more encapsulated services that can be used as building blocks to a larger application. To that end, much of the original edx-platform repository has been split out into micro-frontends, other microservices, plugins, and libraries. However, there are still a number of optional applications within edx-platform and new ones continue to be added.

Decision
--------
From the adoption of this ADR, no new applications should be added into the edx-platform repository without an accompanying ADR explaining why the application cannot be separated out.

Further Guidance
----------------

While the preference should always be to create a new repository for a new application, there are still acceptable reasons why a new application would be better developed within edx-platform:

* The application relates directly to core functionality: course authoring, course administration, or learner-courseware interactions
* The application requires multiple imports from edx-platform

  * If possible, consider if the new application could use querysets returned from api.py instead of directly importing models 
  * If it is truly necessary to import from edx-platform directly, in addition to noting this in the ADR, the authors of the new application should add the libraries or applications it imports from to a sub-document of this ADR. This will help edX and the community prioritize which applications should be broken out. 








