Remove MongoDB as a Dependency
------------------------------

Context
=======

The edx-platform repo uses MongoDB for storing content (the ModuleStore and ContentStore interfaces). MongoDB was chosen early on in the Open edX project because:

* **Course content is very freeform**, and XBlock is a pluggable interface. So while the data stored for videos, problems, crystallography simulations, and circuit schematic editors might have some overlap, individual XBlock are permitted to extend that storage any way they like. At the time, this struck us as a more document-database-centric than SQL.
* **MongoDB’s GridFS** seemed liked a good solution for the static assets that need to be managed on a per-course basis (e.g. PDFs).
* **MySQL at the time did not support JSON fields.** This would have made certain search operations more cumbersome. (MySQL itself was chosen because PostgreSQL was not available on RDS at the time).

Since that time, several things have changed:

#. We've been trying to reduce the complexity of the stack needed to run Open edX.
#. We've switched over from the original ``DraftModuleStore`` to ``DraftVersioningModuleStore``. The latter drops most query patterns and mostly uses MongoDB as a simple key value store.
#. We've adopted django-storages for pluggable file/blob storage.

Decisions
=========

All usage of MongoDB in edx-platform will be removed or replaced in the following ways:

* Old Mongo (``DraftModuleStore``) will be removed as a storage backend altogether. This is already covered under DEPR-58, and affects only old style courses with course keys in the "Org/Course/Run" format (as opposed to the "course-v1:Org+Course+Run" format).
* ContentStore storage of course static assets will be moved to django-storages, allowing for pluggable backends (e.g. files, S3, GridFS).
* Split Modulestore (``DraftVersioningModuleStore``) will be moved to use the Django ORM for the active version lookup, and django-storages to replace key-value storage of what are structure and definition documents today.

Note that this does not include the use of MongoDB for the forums experience. While I still believe that removing MongoDB for that service is desirable, it's beyond the scope of this particular ADR.
