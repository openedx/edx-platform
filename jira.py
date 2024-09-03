import requests
from jira import JIRA

def get_jira_issues(jira_url, api_token, project_key, sprint_id):
    """Fetches JIRA issues based on given criteria.

    Args:
        jira_url (str): The URL of your JIRA instance.
        api_token (str): Your JIRA personal access token.
        project_key (str): The project key.
        sprint_id (str): The sprint ID.

    Returns:
        list: A list of JIRA issues that match the criteria.
    """

    # Authenticate with JIRA
    jira = JIRA(jira_url, basic_auth=(api_token, ""))

    # JQL query to filter issues
    jql = f"assignee is not EMPTY AND project = {project_key} AND sprint = {sprint_id} AND updatedDate < now() - 24h AND comments.created <= now() - 24h"

    # Fetch issues
    issues = jira.search_issues(jql, fields=["key", "summary", "assignee", "updatedDate", "comments"])

    return issues

# Replace with your JIRA instance details
jira_url = "https://your-jira-instance.atlassian.net"
api_token = "your-api-token"
project_key = "your-project-key"
sprint_id = "your-sprint-id"

issues = get_jira_issues(jira_url, api_token, project_key, sprint_id)

for issue in issues:
    print(f"Issue Key: {issue.key}")
    print(f"Summary: {issue.fields.summary}")
    print(f"Assignee: {issue.fields.assignee.key}")
    print(f"Updated Date: {issue.fields.updated}")
    print(f"Comments: {len(issue.fields.comments)}")
    print()
