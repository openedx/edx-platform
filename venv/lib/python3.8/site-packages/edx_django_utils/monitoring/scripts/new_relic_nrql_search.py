"""
This script takes a regex to search through the NRQL of New Relic alert policies
and New dashboards.

This script makes use of New Relic's GraphQL API. See https://api.newrelic.com/graphiql.

For help::

    python edx_django_utils/monitoring/scripts/new_relic_nrql_search.py --help

"""
import json
import os
import re
from string import Template

import click
import requests


@click.command()
@click.option(
    '--regex',
    required=True,
    help="The regex to use to search NRQL in alert policies and dashboards.",
)
@click.option(
    '--policy_id',
    multiple=True,
    help="Optionally provide a specific policy id to check. Multiple can be supplied.",
)
@click.option(
    '--dashboard_guid',
    multiple=True,
    help="Optionally provide a specific dashboard guid to check. Multiple can be supplied.",
)
def main(regex, policy_id, dashboard_guid):
    """
    Search NRQL in New Relic alert policies and dashboards using regex.

    Example usage:

        new_relic_nrql_search.py --regex tnl

    Note: The search ignores case since NRQL is case insensitive.

    Pre-requisite, set the following environment variable (in a safe way):

        NEW_RELIC_API_KEY=XXXXXXX

    See https://docs.newrelic.com/docs/apis/intro-apis/new-relic-api-keys/#user-api-key for details
    on setting an API key.

    To skip alert policies or dashboards, just use a non-existent id, like --policy_id 0 or --dashboard_guid 0.

    """
    # Set environment variables
    api_key = os.environ['NEW_RELIC_API_KEY']
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
    }

    compiled_regex = re.compile(regex)

    account_ids = get_account_ids(headers)
    for account_id in account_ids:
        search_alert_policies(compiled_regex, account_id, headers, policy_id)
    print()
    search_dashboards(compiled_regex, headers, dashboard_guid)
    print(flush=True)


def get_account_ids(headers):
    """
    Returns a list of the New Relic account ids to be searched.
    """
    response = requests.get(
        'https://api.newrelic.com/graphql',
        headers=headers,
        params={'query': """
            {
              actor {
                accounts {
                  id
                }
              }
            }
        """},
    )
    response.raise_for_status()  # could be an error response
    response_data = response.json()
    account_ids = [account['id'] for account in response_data['data']['actor']['accounts']]
    return account_ids


# Template with variables:
# - account_id
# - cursor; can be null or cursor string
ALERT_POLICY_LIST_TEMPLATE = Template("""
    {
      actor {
        account(id: ${account_id}) {
          alerts {
            policiesSearch(cursor: ${cursor}) {
              policies {
                id
                name
              }
              nextCursor
            }
          }
        }
      }
    }
""")

# Template with variables:
# - account_id
# - policy_id
NRQL_ALERT_CONDITIONS_TEMPLATE = Template("""
    {
      actor {
        account(id: ${account_id}) {
          alerts {
            nrqlConditionsSearch(searchCriteria: {policyId: ${policy_id}}) {
              nrqlConditions {
                nrql {
                  query
                }
                name
              }
            }
          }
        }
      }
    }
""")


def search_alert_policies(regex, account_id, headers, policy_id):
    """
    Searches New Relic alert policy NRQL using the regex argument.

    Arguments:
        regex (re.Pattern): compiled regex used to compare against NRQL
        account_id (int): the id of the New Relic account in which to search.
        headers (dict): headers required to make http requests to New Relic.
        policy_id (tuple): optional tuple of policy ids supplied from the command-line.
    """
    policies = []
    cursor = 'null'
    while True:
        response = requests.get(
            'https://api.newrelic.com/graphql',
            headers=headers,
            params={'query': ALERT_POLICY_LIST_TEMPLATE.substitute(
                account_id=account_id,
                cursor=cursor
            )},
        )
        response.raise_for_status()  # could be an error response
        response_data = response.json()
        query_results = response_data['data']['actor']['account']['alerts']['policiesSearch']
        policies += query_results['policies']
        if not query_results['nextCursor']:
            break
        cursor = f"\"{query_results['nextCursor']}\""
    # Note: policy_id is an optional tuple of policy ids supplied from the command-line.
    if policy_id:
        policies = [policy for policy in policies if policy['id'] in policy_id]
    print(f"Searching for regex {regex.pattern} in {len(policies)} alert policies in account {account_id}...")
    policy_ids_printed = {}
    for policy in policies:
        print('.', end='', flush=True)

        # get the NRQL alert conditions from the alert policy
        response = requests.get(
            'https://api.newrelic.com/graphql',
            headers=headers,
            params={'query': NRQL_ALERT_CONDITIONS_TEMPLATE.substitute(
                account_id=account_id,
                policy_id=policy['id'],
            )},
        )
        response.raise_for_status()  # could be an error response
        response_data = response.json()

        nrql_conditions = response_data['data']['actor']['account']['alerts']['nrqlConditionsSearch']['nrqlConditions']
        for nrql_condition in nrql_conditions:
            nrql_query = nrql_condition['nrql']['query']
            if regex.search(nrql_query, re.IGNORECASE):

                # Print the alert policy header for the first alert condition matched
                if policy['id'] not in policy_ids_printed:
                    policy_ids_printed[policy['id']] = True
                    print('\n')
                    print(
                        f"Found in \"{policy['name']}\" "
                        # NOTE: The API doesn't provide a link to the policy, so this is a static link to
                        #   the alert policies home page.
                        f"(policy_id={policy['id']}, search_link=https://one.nr/0X8woZOZvQx):"
                    )
                    print('')

                # Print the alert condition that matched
                print(f"- {nrql_condition['name']}: {nrql_query}")

    if policy_ids_printed:
        command_line = ''
        for policy_id in policy_ids_printed.keys():
            command_line += f'--policy_id {policy_id} '
        print("\n\nRun again with found policies: {}".format(command_line))
    else:
        print("\n\nNo alert policies matched.")


# Retrieves list of dashboard and dashboard page entities
# Template with variable cursor; can be null or cursor string
DASHBOARD_LIST_QUERY_TEMPLATE = Template("""
    {
      actor {
        entitySearch(queryBuilder: {type: DASHBOARD}) {
          results(cursor: ${cursor}) {
            entities {
              ... on DashboardEntityOutline {
                guid
                name
                accountId
                dashboardParentGuid
                permalink
              }
            }
            nextCursor
          }
          count
        }
      }
    }
""")

# Retrieves dashboard entities. Does not work for dashboard pages.
DASHBOARD_ENTITY_QUERY = """
    query ($guids: EntityGuid!) {
      actor {
        entities(guids: $guids) {
          ... on DashboardEntity {
            guid
            pages {
              widgets {
                rawConfiguration
                title
              }
            }
            name
          }
        }
      }
    }
"""


def search_dashboards(regex, headers, dashboard_guid):
    """
    Searches New Relic alert policy NRQL using the regex argument.

    Arguments:
        regex (re.Pattern): compiled regex used to compare against NRQL
        headers (dict): headers required to make http requests to New Relic
        dashboard_guid (tuple): optional tuple of dashboard guids supplied from the command-line.
    """
    # load details of all dashboards
    dashboards = []
    cursor = 'null'
    while True:
        response = requests.get(
            'https://api.newrelic.com/graphql',
            headers=headers,
            params={'query': DASHBOARD_LIST_QUERY_TEMPLATE.substitute(cursor=cursor)},
        )
        response.raise_for_status()  # could be an error response
        response_data = response.json()
        query_results = response_data['data']['actor']['entitySearch']['results']
        dashboards += query_results['entities']
        if not query_results['nextCursor']:
            break
        cursor = f"\"{query_results['nextCursor']}\""
    # Filter out dashboard pages, which the dashboard entity query will not be able to find.
    # - Note: This could probably be handled in the original query, but not sure how.
    dashboards = [dashboard for dashboard in dashboards if dashboard['dashboardParentGuid'] is None]
    # Note: dashboard_guid is an optional tuple of dashboard guids supplied from the command-line.
    if dashboard_guid:
        dashboards = [dashboard for dashboard in dashboards if dashboard['guid'] in dashboard_guid]
    print(f"Searching for regex {regex.pattern} in {len(dashboards)} dashboards...")
    dashboard_guids_printed = {}
    for dashboard in dashboards:
        print('.', end='', flush=True)

        # get the dashboard details
        response = requests.get(
            'https://api.newrelic.com/graphql',
            headers=headers,
            params={
                'query': DASHBOARD_ENTITY_QUERY,
                'variables': json.dumps({'guids': dashboard['guid']}),
            }
        )
        response.raise_for_status()  # could be an error response
        response_data = response.json()

        if response_data['data']['actor']['entities'][0]['pages']:
            for page in response_data['data']['actor']['entities'][0]['pages']:
                for widget in page['widgets']:
                    if 'nrqlQueries' not in widget['rawConfiguration']:
                        continue

                    for nrql_query in widget['rawConfiguration']['nrqlQueries']:
                        query = nrql_query['query']
                        if regex.search(query, re.IGNORECASE):

                            # Print the dashboard header for the first widget nrql that matches
                            if dashboard['guid'] not in dashboard_guids_printed:
                                dashboard_guids_printed[dashboard['guid']] = True
                                print('\n')
                                print(
                                    f"Found in \"{dashboard['name']}\" "
                                    f"(guid={dashboard['guid']}, link={dashboard['permalink']}):"
                                )
                                print('')

                            # Print the widget NRQL that matches
                            print(f"- {widget['title']}: {query}")

    if dashboard_guids_printed:
        command_line = ''
        for dashboard_guid in dashboard_guids_printed.keys():
            command_line += f'--dashboard_guid {dashboard_guid} '
        print("\n\nRun again with found dashboards: {}".format(command_line))
    else:
        print("\n\nNo dashboards found that match.")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
