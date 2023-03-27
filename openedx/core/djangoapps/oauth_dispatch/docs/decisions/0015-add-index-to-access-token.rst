15. Add index to AccessToken table
##################################

Status
------

Accepted

Context
-------
The `edx_clear_expired_tokens` management command seeks to keep the AccessToken and RefreshToken tables manageable by removing expired
or revoked tokens. If those tables have been allowed to grow unchecked for a sufficiently long time, this command becomes prohibitively
slow.
One cause of slowness is a join between the two tables that then filters on the AccessToken.expires field. In the library, this field does
not have an index.

Decisions
---------

We will add a migration that uses RunSQL to add an index on the `expires` field of the AccessToken table.

Consequences
------------

* If django-oauth-toolkit updates AccessToken to have an index on the same field, it's possible there could be a conflict.
However, assuming this is done through the ORM and automatic Django migrations, Django will usually apply a hash at the end
of the name of the index, thus avoiding a collision.
* There will be a mismatch between what is in the database and what is specified in code for the AccessToken model

Rejected Alternatives
---------------------
* Wrapping the AccessToken class in a custom model and adding db_index=True on the expires field in the wrapper class

This would require us to maintain the new class throughout changes in the AccessToken library and conceivably have to
rewrite a fair amount of code to use the new wrapped model.

* Forking the django-oauth-toolkit library and adding db_index=True on the expires field

Maintaining a fork would require a lot of overhead and was deemed not worth the effort.

* Submitting an issue to django-oauth-toolkit

We may yet submit a new issue, but we do not know how long that turnaround time would be. For installations where the table
is already large, delays in adding the index will only worsen the problem.
