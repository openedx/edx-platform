Purpose of App: plugins
=======================

Status
------

Accepted

Context
-------

.. note:: This doc was written long after this app was created, thus explaining the past tense in language below.

When this was created, the only way to add another app to lms/cms was to create the app in edx-platform repo. This was untenible due to already large size of edx-platform and adding another app increased the chance of further entanglement between the different apps.

Decision
--------

It was decided the ability to add django apps as plugins was necessary.

Consequences
------------

This would make it easier to move code for some critical/key apps outside of edx-platform and into their on repository. It would also make it easier to add further functionality into lms/cms without needing to change any code in edx-platform.