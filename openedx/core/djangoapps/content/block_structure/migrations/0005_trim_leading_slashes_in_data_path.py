"""
Data migration to convert absolute paths in block_structure.data to be relative.

This has only been tested with MySQL, though it should also work for Postgres as
well. This is necessary to manually correct absolute paths in the "data" field
of the block_structure table. For S3 storage, having a path that starts with
"/courses/" puts things in the same place as a path starting with "courses/",
but absolute paths are not permitted for FileFields.

These values would have always been broken in devstack (because it's not in
MEDIA_ROOT), but it used to work for the S3 storages option because the security
checking happened at the storage layer, and the path is equivalent in S3 because
we just append either value to the bucket's root.

However, in Django > 2.2.20, this checking against absolute paths has been added
to the FileField itself, and an upgrade attempt started causing write failures
to Block Structures.

There are separate PRs to fix the config values so that new writes start with a
"courses/" prefix. This migration to is fix old entries by removing any leading
"/" characters.

THIS MIGRATION MUST BE RUN BEFORE UPGRADING TO DJANGO > 2.2.20 IF YOU ARE
USING A STORAGE_CLASS IN BLOCK_STRUCTURES_SETTINGS. If you do not specify this
setting and only run Block Structures out of memcached, this should not affect
you.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('block_structure', '0004_blockstructuremodel_usagekeywithrun'),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE block_structure
                SET data = right(data, length(data) - 1)
                WHERE data like '/%';
            """
        )
    ]
