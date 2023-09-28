from django.db import migrations


def load_system_defined_org_taxonomies(apps, _schema_editor):
    """
    Associates the system defined taxonomy Language (id=-1) to all orgs and
    removes the ContentOrganizationTaxonomy (id=-3) from the database
    """
    TaxonomyOrg = apps.get_model("content_tagging", "TaxonomyOrg")
    TaxonomyOrg.objects.create(id=-1, taxonomy_id=-1, org=None)

    Taxonomy = apps.get_model("oel_tagging", "Taxonomy")
    Taxonomy.objects.get(id=-3).delete()




def revert_system_defined_org_taxonomies(apps, _schema_editor):
    """
    Deletes association of system defined taxonomy Language (id=-1) to all orgs and
    creates the ContentOrganizationTaxonomy (id=-3) in the database
    """
    TaxonomyOrg = apps.get_model("content_tagging", "TaxonomyOrg")
    TaxonomyOrg.objects.get(id=-1).delete()

    Taxonomy = apps.get_model("oel_tagging", "Taxonomy")
    org_taxonomy = Taxonomy(
        pk=-3,
        name="Organizations",
        description="Allows tags for any organization ID created on the instance.",
        enabled=True,
        required=True,
        allow_multiple=False,
        allow_free_text=False,
        visible_to_authors=False,
    )
    ContentOrganizationTaxonomy = apps.get_model("content_tagging", "ContentOrganizationTaxonomy")
    org_taxonomy.taxonomy_class = ContentOrganizationTaxonomy
    org_taxonomy.save()


class Migration(migrations.Migration):
    dependencies = [
        ("content_tagging", "0003_system_defined_fixture"),
    ]

    operations = [
        migrations.RunPython(load_system_defined_org_taxonomies, revert_system_defined_org_taxonomies),
    ]
