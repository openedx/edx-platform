"""
Temporary import path shim module.

Previously, the safe_lxml package was housed in common/lib/safe_lxml.
It was installed as its own Python project, so instead of its import path
being, as one would expect:

    import common.lib.safe_lxml.safe_lxml

it was instead just:

    import safe_lxml

To increase the sanity of edx-platform and simplify its tooling, we are
moving the safe_lxml package to openedx/core/lib (in tihs same repo) and
changing its import path to:

    import openedx.core.lib.safe_lxml

In order to maintain backwards-compatibility with code using the
old import path for one release, we expose this compatibility module.

Jira ticket (public, but requires account): https://openedx.atlassian.net/browse/BOM-2583
Target removal for this shim module: by Olive.
"""

from openedx.core.lib.safe_lxml import *  # pylint: disable=unused-wildcard-import,wrong-import-order
