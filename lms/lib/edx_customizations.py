"""
Edx customizations for the LMS.

Note: In order to enable rollout of new mappings from request path to
  NewRelic app name suffix via config, this module may contain multiple
  implementations (the current and the last).  This enables quick rollback
  via config.

TODO:
1. Move this file out of edx-platform and into a plugin.
2. The following may move into an ADR at that time.

Decisions:

* We’ll start with a team-based split of the LMS at first, rather than domain based.
  * We can always change it to a different orientation if that has issues.
* All new apps should have apdex and error alerting routed to a team.

Goals:

* Enables simpler alerting and on-call configuration for team ownership inside edx-platform.
* All parts of edx-platform should be owned and nothing should end up in the default app.

"""
import re
from enum import Enum


class AppNameSuffix(Enum):
    bom_squad = 'bom-squad'


SINGLE_REQUEST_PATH_REGEX_TO_SUFFIX_MAPPINGS = [
    # /api-admin/api/v1/api_access_request/
    (re.compile(r'^\/api-admin\/api\/v1\/api_access_request\/?$'), AppNameSuffix.bom_squad),
]


def newrelic_single_app_name_suffix_handler(request_path):
    """
    Takes a request path and returns the mapped NewRelic app name suffix if any is found.

    This implementation has a single mapping for initial rollout testing.
    """
    for path_regex, suffix in SINGLE_REQUEST_PATH_REGEX_TO_SUFFIX_MAPPINGS:
        if path_regex.search(request_path):
            return suffix.value

    return None
