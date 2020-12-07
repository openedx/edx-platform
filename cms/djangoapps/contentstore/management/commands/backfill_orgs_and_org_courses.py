"""
A backfill command to migrate Open edX instances to the new world of
"organizations are enabled everywhere".

For full context, see:
https://github.com/edx/edx-organizations/blob/master/docs/decisions/0001-phase-in-db-backed-organizations-to-all.rst
"""
from django.core.management import BaseCommand, CommandError
from organizations import api as organizations_api

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Back-populate edx-organizations models from existing course runs & content libraries.

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

    # Make help  message the first line of docstring.
    # I'd like to include the entire docstring but Django omits the newlines,
    # so it looks pretty bad.
    help = __doc__.strip().splitlines()[0]

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help="Apply backfill to database without prompting for confirmation."
        )
        parser.add_argument(
            '--dry',
            action='store_true',
            help="Show backfill, but do not apply changes to database."
        )

    def handle(self, *args, **options):
        """
        Handle the backfill command.
        """
        orgslug_coursekey_pairs = find_orgslug_coursekey_pairs()
        orgslug_library_pairs = find_orgslug_library_pairs()
        orgslugs = (
            {orgslug for orgslug, _ in orgslug_coursekey_pairs} |
            {orgslug for orgslug, _ in orgslug_library_pairs}
        )
        # Note: the `organizations.api.bulk_add_*` code will handle:
        # * not overwriting existing organizations, and
        # * skipping duplicates, based on the short name (case-insensiive),
        # so we don't have to worry about those here.
        orgs = [
            {"short_name": orgslug, "name": orgslug}
            # The `sorted` calls aren't strictly necessary, but they'll help make this
            # function more deterministic in case something goes wrong.
            for orgslug in sorted(orgslugs)
        ]
        org_coursekey_pairs = [
            ({"short_name": orgslug}, coursekey)
            for orgslug, coursekey in sorted(orgslug_coursekey_pairs)
        ]
        if not confirm_changes(options, orgs, org_coursekey_pairs):
            print("No changes applied.")
            return
        print("Applying changes...")
        organizations_api.bulk_add_organizations(orgs, dry_run=False)
        organizations_api.bulk_add_organization_courses(org_coursekey_pairs, dry_run=False)
        print("Changes applied successfully.")


def confirm_changes(options, orgs, org_coursekey_pairs):
    """
    Should we apply the changes to the database?

    If `--apply`, this just returns True.
    If `--dry`, this does a dry run and then returns False.
    Otherwise, it does a dry run and then prompts the user.

    Arguments:
        options (dict[str]): command-line arguments.
        orgs (list[dict]): list of org data dictionaries to bulk-add.
        org_coursekey_pairs (list[tuple[dict, CourseKey]]):
            list of (org data dictionary, course key) links to bulk-add.

    Returns: bool
    """
    if options.get('apply') and options.get('dry'):
        raise CommandError("Only one of 'apply' and 'dry' may be specified")
    if options.get('apply'):
        return True
    organizations_api.bulk_add_organizations(orgs, dry_run=True)
    organizations_api.bulk_add_organization_courses(org_coursekey_pairs, dry_run=True)
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
