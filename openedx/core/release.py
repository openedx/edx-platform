"""
Information about the release line of this Open edX code.
"""

# The release line: an Open edX release name ("ficus"), or "master".
RELEASE_LINE = "master"


def doc_version():
    """The readthedocs.org version name used in documentation references.

    Returns a short string like "latest" or "open-release-ficus.master".
    """
    if RELEASE_LINE == "master":
        return "latest"
    else:
        return "open-release-{}.master".format(RELEASE_LINE)
