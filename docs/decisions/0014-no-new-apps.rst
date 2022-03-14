14. Documentation of new apps in edx-platform

Status
------
In Review

Context
-------
In recent years, edX and the software industry as a whole have been moving away from a monolith structure towards more modular architecture to more encapsulated services that can be used as building blocks to a larger application. To that end, much of the original edx-platform repository has been split out into micro-frontends, other microservices, plugins, and libraries. However, there are still a number of optional applications within edx-platform and new ones continue to be added.

Decision
--------
From the adoption of this ADR, no new applications should be added into the edx-platform repository without an accompanying ADR explaining why the application cannot be separated out.

More Stuff
----------
While there is no hard-and-fast rule for what new functionality should stay in edx-platform versus being broken out, there are a few guidelines that may be useful:
- if a new application requires importing non-core models from edx-platform, it should stay in edx-platform and add the thing it depends on to a list
- apps that deal with core functionality: Course Authoring, Course Administration, Learner Courseware interactions







