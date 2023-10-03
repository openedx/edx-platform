""" Helper functions for drf-spectacular """


def cms_api_filter(endpoints):
    """
    At the moment, we are only enabling drf-spectacular for the CMS API.
    Filter out endpoints that are not part of the CMS API.
    """
    filtered = []
    for (path, path_regex, method, callback) in endpoints:
        # Add only paths to the list that are part of the CMS API
        if (
            path.startswith("/api/contentstore/v1/xblock") or
            path.startswith("/api/contentstore/v1/videos") or
            path.startswith("/api/contentstore/v1/video_transcripts") or
            path.startswith("/api/contentstore/v1/file_assets")
        ):
            filtered.append((path, path_regex, method, callback))
    return filtered
