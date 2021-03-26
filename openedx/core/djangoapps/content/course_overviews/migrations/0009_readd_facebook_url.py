from django.db import migrations, models, connection

def table_description():
    """Handle Mysql/Pg vs Sqlite"""
    # django's mysql/pg introspection.get_table_description tries to select *
    # from table and fails during initial migrations from scratch.
    # sqlite does not have this failure, so we can use the API.
    # For not-sqlite, query information-schema directly with code lifted
    # from the internals of django.db.backends.mysql.introspection.py

    if connection.vendor == 'sqlite':
        fields = connection.introspection.get_table_description(connection.cursor(), 'course_overviews_courseoverview')
        return [f.name for f in fields]
    else:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'course_overviews_courseoverview' AND table_schema = DATABASE()""")
        rows = cursor.fetchall()
        return [r[0] for r in rows]


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0008_remove_courseoverview_facebook_url'),
    ]

    # An original version of 0008 removed the facebook_url field We need to
    # handle the case where our noop 0008 ran AND the case where the original
    # 0008 ran.  We do that by using the standard information_schema to find out
    # what columns exist. _meta is unavailable as the column has already been
    # removed from the model
    operations = []
    fields = table_description()

    # during a migration from scratch, fields will be empty, but we do not want to add
    # an additional facebook_url
    if fields and not any(f == 'facebook_url' for f in fields):
        operations += migrations.AddField(
            model_name='courseoverview',
            name='facebook_url',
            field=models.TextField(null=True),
        ),
