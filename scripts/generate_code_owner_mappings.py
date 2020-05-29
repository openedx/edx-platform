"""
This script generates code owner mappings for monitoring LMS.

Sample usage::

    python scripts/generate_code_owner_mappings.py

Sample CSV input::

    Path,owner.squad
    ./common/djangoapps/xblock_django,team-red
    ./openedx/core/djangoapps/xblock,team-red
    ./lms/djangoapps/badges,team-blue

Sample output::

    # Copy results into appropriate config yml file.
    # Note: printed in reverse order so catch-alls will be checked last.
    CODE_OWNER_MAPPINGS:
    - - xblock_django
      - team-red
    - - openedx.core.djangoapps.xblock
      - team-red
    - - badges
      - team-blue

"""
import re

import csv
import click


@click.command()
@click.option(
    '--app-csv',
    help="File name of .csv file from edx-platform App ownership sheet",
    default='Squad-based Tech Ownership Assignment - 2020 - edx-platform Apps Ownership.csv'
)
def main(app_csv):
    """
    Reads CSV of ownership data and outputs config.yml setting to system.out.
    """
    csv_data = None
    with open(app_csv, 'r') as file:
        csv_data = file.read()
    reader = csv.DictReader(csv_data.splitlines())

    output_list = []
    for row in reader:
        # Try to use the 'email' field to identify the user.  If it's not present, use 'username'.
        path = row.get('Path')
        squad = row.get('owner.squad')

        may_have_views = re.match(r'.*djangoapps', path) or re.match(r'[./]*openedx\/features', path)
        may_have_views = may_have_views and not re.match(r'.*(\/tests\b|cms\/).*', path)
        if may_have_views:
            path = path.replace('./', '')  # remove ./ from beginning of path
            path = path.replace('lms/djangoapps/', '')  # not included in final module name
            path = path.replace('common/djangoapps/', '')  # not included in final module name
            path = path.replace('/', '.')  # convert path to dotted module name

            output_list.append((path, squad))

    output_list.sort(reverse=True)
    print('# Copy results into appropriate config yml file.')
    print('# Note: printed in reverse order so catch-alls will be checked last.')
    print('CODE_OWNER_MAPPINGS:')
    for path, squad in output_list:
        print("- - {}".format(path))
        print("  - {}".format(squad))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
