""" Helper functions for drf-spectacular """


def lms_api_filter(endpoints):
    """
    At the moment, we are only enabling drf-spectacular for the CMS API.
    Filter out endpoints that are not part of the CMS API.
    """
    filtered = []
    for (path, path_regex, method, callback) in endpoints:
        # Add only paths to the list that are part of the CMS API
        if (
            # Don't just replace this with /v1 when switching to a later version of the CMS API.
            # That would include some unintended endpoints.
            path.startswith("/courses/")
        ):
            filtered.append((path, path_regex, method, callback))
    return filtered
