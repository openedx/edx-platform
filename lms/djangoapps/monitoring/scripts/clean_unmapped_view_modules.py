"""
Provided a CSV of data from our monitoring system, this script outputs a unique and clean
set of apps of unmapped view_func_modules.

Context: This script was useful when first introducing ownership mapping and we had many
apps from 3rd-party dependencies that were missed. At this point, we'd probably only
expect 0-2 new unmapped apps, which could be cleaned manually very quickly without this
script.

Sample usage::

    python lms/djangoapps/monitoring/scripts/clean_unmapped_view_modules.py --unmapped-csv "unmapped-apps.csv"

Or for more details::

    python lms/djangoapps/monitoring/scripts/clean_unmapped_view_modules.py --help


"""
import csv
import click


@click.command()
@click.option(
    '--unmapped-csv',
    help="File name of .csv file with unmapped edx-platform view modules.",
    required=True
)
def main(unmapped_csv):
    """
    Reads CSV of unmapped view_func_modules and outputs a clean list of apps to map.

    NewRelic Insights Query to create CSV of unmapped modules:

        \b
        SELECT count(view_func_module) FROM Transaction
        WHERE code_owner is null FACET view_func_module
        SINCE 1 week ago
        LIMIT 50

        \b
        * Increase or decrease SINCE clause as necessary based on when the mappings were last updated.
        * Save results as CSV for use in script

    Sample CSV input::

        \b
        View Func Module,View Func Modules
        enterprise.api.v1.views,1542
        edx_proctoring.views,116
        social_django.views,53

    Script removes duplicates in addition to providing sorted list of plain app names.

    """
    with open(unmapped_csv, 'r') as file:
        csv_data = file.read()
    reader = csv.DictReader(csv_data.splitlines())

    clean_apps_set = set()
    for row in reader:
        path = row.get('View Func Module')
        path_parts = path.split('.')
        clean_apps_set.add(path_parts[0])

    print('# Move into generate_code_owner_mappings.py and complete mappings.')
    for clean_app in sorted(clean_apps_set):
        print(clean_app)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
