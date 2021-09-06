# -*- coding: utf-8 -*-


from django.db import migrations, models


def add_default_enable(apps, schema_editor):
    ForumsConfig = apps.get_model("django_comment_common", "ForumsConfig")
    settings_count = ForumsConfig.objects.count()
    if settings_count == 0:
        # By default we want the comment client enabled, but this is *not* enabling
        # discussions themselves by default, as in showing the Disucussions tab, or
        # inline discussions, etc.  It just allows the underlying service client to work.
        settings = ForumsConfig(enabled=True)
        settings.save()


def reverse_noop(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('django_comment_common', '0002_forumsconfig'),
    ]

    operations = [
        migrations.RunPython(add_default_enable, reverse_code=reverse_noop),
    ]
