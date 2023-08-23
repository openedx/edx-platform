from django.db import migrations


def load_system_defined_org_taxonomies(apps, _schema_editor):
    """
    Associates the system defined taxonomy Language (id=-1) to all orgs
    """
    TaxonomyOrg = apps.get_model("content_tagging", "TaxonomyOrg")

    TaxonomyOrg.objects.create(id=-1, taxonomy_id=-1, org=None)


def revert_system_defined_org_taxonomies(apps, _schema_editor):
    """
    Deletes association of system defined taxonomy Language (id=-1) to all orgs
    """
    TaxonomyOrg = apps.get_model("content_tagging", "TaxonomyOrg")

    TaxonomyOrg.objects.get(id=-1).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("content_tagging", "0003_system_defined_fixture"),
    ]

    operations = [
        migrations.RunPython(load_system_defined_org_taxonomies, revert_system_defined_org_taxonomies),
    ]
