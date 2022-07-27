"""
Temporary import path shim module for openedx.core.lib.safe_lxml.

Previously, the safe_lxml package was housed in common/lib/safe_lxml.
It was installed as its own Python project, so instead of its import path
being, as one would expect:

    import common.lib.safe_lxml.safe_lxml

it was instead just:

    import safe_lxml

To increase the sanity of edx-platform and simplify its tooling, we have
moved the safe_lxml package to openedx/core/lib (in tihs same repo) and
changing its import path to:

    import openedx.core.lib.safe_lxml

For details, see:
https://openedx.atlassian.net/browse/BOM-2583 (public, but requires account)

In order to maintain backwards-compatibility with code using the
old import path for one release, we expose this temporary compatibility
module and raise a warning when the old import path is used.
This entire `safe_lxml` shim folder can be removed after 2023-01-01.
In the Poplar release, 'import safe_lxml' will stop working entirely.
"""
import warnings

warnings.warn(
    "Importing from 'safe_lxml' instead of 'openedx.core.lib.safe_lxml' is deprecated.",
    stacklevel=3,  # Should surface the line that is doing the importing.
)

from openedx.core.lib.safe_lxml import *  # pylint: disable=unused-wildcard-import,wrong-import-order
