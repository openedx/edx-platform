"""
A backfill command to migrate Open edX instances to the new world of
"organizations are enabled everywhere".

For full context, see:
https://github.com/edx/edx-organizations/blob/master/docs/decisions/0001-phase-in-db-backed-organizations-to-all.rst
"""
from textwrap import dedent

from django.core.management import BaseCommand, CommandError
from organizations import api as organizations_api

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Back-populate edx-organizations models from existing courses & content libraries.

    Before the Lilac open release, Open edX instances by default did not make
    use of the models in edx-organizations.
    In Lilac and beyond, the edx-organizations models are enabled globally.

    This command exists to migrate pre-Lilac instances that did not enable
    `FEATURES['ORGANIZATIONS_APP']`.
    It automatically creates all missing Organization and OrganizationCourse
    instances based on the course runs in the system (loaded from CourseOverview)
    and the V1 content libraries in the system (loaded from the Modulestore).

    Organizations created by this command will have their `short_name` and
    `name` equal to the `org` part of the library/course key that triggered
    their creation. For example, given an Open edX instance with the course run
    `course-v1:myOrg+myCourse+myRun` but no such Organization with the short name
    "myOrg" (case-insensitive), this command will create the following
    organization:
        > Organization(
        >     short_name='myOrg',
        >     name='myOrg',
        >     description=None,
        >     logo=None,
        >     active=True,
        > )
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help="Apply backfill to database (instead of just showing the changes)."
        )
        parser.add_argument(
            '--dry',
            action='store_true',
            help="Apply backfill to database (instead of just showing the changes)."
        )

    def handle(self, *args, **options):

        # Find `orgs` and `org_coursekey_pairs` to be bulk-added.
        # The `sorted` calls aren't strictly necessary, but they'll help make this
        # function more deterministic in case something goes wrong.
        orgslug_coursekey_pairs = find_orgslug_coursekey_pairs()
        orgslug_library_pairs = find_orgslug_library_pairs()
        orgslugs = (
            {orgslug for orgslug, _ in orgslug_coursekey_pairs} |
            {orgslug for orgslug, _ in orgslug_library_pairs}
        )
        orgs = [
            {"short_name": orgslug, "name": orgslug}
            for orgslug in sorted(orgslugs)
        ]
        org_coursekey_pairs = [
            ({"short_name": orgslug}, coursekey)
            for orgslug, coursekey in sorted(orgslug_coursekey_pairs)
        ]

        # Note that edx-organizations code will handle:
        # * Not overwriting existing organizations.
        # * Skipping duplicates, based on the short name (case-insensiive).

        # Start with a dry run.
        # This will log to the user which orgs/org-courses will be created/reactivated.
        organizations_api.bulk_add_organizations(
            orgs,
            dry_run=True,
        )
        organizations_api.bulk_add_organization_courses(
            org_coursekey_pairs,
            dry_run=True,
        )
        if not should_apply_changes(options):
            print("No changes applied.")
            return

        # It's go time.
        print("Applying changes...")
        organizations_api.bulk_add_organizations(
            orgs,
            dry_run=False,
        )
        organizations_api.bulk_add_organization_courses(
            org_coursekey_pairs,
            dry_run=False,
        )
        print("Changes applied successfully.")


def should_apply_changes(options):
    """
    Should we apply the changes to the db?

    If already specified on the command line, use that value.

    Otherwise, prompt.
    """
    if options.get('apply') and options.get('dry'):
        raise CommandError("Only one of 'apply' and 'dry' may be specified")
    if options.get('apply'):
        return True
    if options.get('dry'):
        return False
    answer = ""
    while answer.lower() not in {'y', 'yes', 'n', 'no'}:
        answer = input('Commit changes shown above to the database [y/n]? ')
    return answer.lower().startswith('y')


def find_orgslug_coursekey_pairs():
    """
    Returns the unique pairs of (organization short name, course run key)
    from the CourseOverviews table, which should contain all course runs in the
    system.

    Returns: set[tuple[str, CourseKey]]
    """
    # Using a set comprehension removes any duplicate (org, course) pairs.
    return {
        (course_key.org, course_key)
        for course_key
        # Worth noting: This will load all CourseOverviews, no matter their VERSION.
        # This is intentional: there may be course runs that haven't updated
        # their CourseOverviews entry since the last schema change; we still want
        # capture those course runs.
        in CourseOverview.objects.all().values_list("id", flat=True)
    }


def find_orgslug_library_pairs():
    """
    Returns the unique pairs of (organization short name, content library key)
    from the modulestore.

    Note that this only considers "version 1" (aka "legacy" or "modulestore-based")
    content libraries.
    We do not consider "version 2" (aka "blockstore-based") content libraries,
    because those require a database-level link to their authoring organization,
    and thus would not need backfilling via this command.

    Returns: set[tuple[str, LibraryLocator]]
    """
    # Using a set comprehension removes any duplicate (org, library) pairs.
    return {
        (library_key.org, library_key)
        for library_key
        in modulestore().get_library_keys()
    }
