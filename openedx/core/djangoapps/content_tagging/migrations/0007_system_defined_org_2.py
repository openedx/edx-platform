from django.db import migrations


def mark_language_taxonomy_as_all_orgs(apps, _schema_editor):
    """
    Associates the system defined taxonomy Language (id=-1) to all orgs.
    """
    TaxonomyOrg = apps.get_model("content_tagging", "TaxonomyOrg")
    TaxonomyOrg.objects.update_or_create(taxonomy_id=-1, defaults={"org": None})


def revert_mark_language_taxonomy_as_all_orgs(apps, _schema_editor):
    """
    Deletes association of system defined taxonomy Language (id=-1) to all orgs.
    """
    TaxonomyOrg = apps.get_model("content_tagging", "TaxonomyOrg")
    TaxonomyOrg.objects.get(taxonomy_id=-1, org=None).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content_tagging', '0001_squashed'),
        ("oel_tagging", "0012_language_taxonomy"),
    ]

    operations = [
        migrations.RunPython(mark_language_taxonomy_as_all_orgs, revert_mark_language_taxonomy_as_all_orgs),
    ]
