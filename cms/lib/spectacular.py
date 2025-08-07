"""Helper functions for drf-spectacular"""

import re


def cms_api_filter(endpoints):
    """
    At the moment, we are only enabling drf-spectacular for the CMS API.
    Filter out endpoints that are not part of the CMS API.
    """
    filtered = []
    CMS_PATH_PATTERN = re.compile(
        r"^/api/contentstore/v0/(xblock|videos|video_transcripts|file_assets|youtube_transcripts)"
    )

    for path, path_regex, method, callback in endpoints:
        if CMS_PATH_PATTERN.match(path) or (
            path.startswith("/api/courses/")
            and "bulk_enable_disable_discussions" in path
        ):
            filtered.append((path, path_regex, method, callback))

    return filtered
