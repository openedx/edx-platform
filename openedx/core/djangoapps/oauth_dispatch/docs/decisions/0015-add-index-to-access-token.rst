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

Rejected Alternatives
---------------------
