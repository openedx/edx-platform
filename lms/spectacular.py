""" Helper functions for drf-spectacular """


def lms_api_filter(endpoints):
    """
    At the moment, we are only enabling drf-spectacular for the LMS INSTRUCTOR APIs.
    """
    filtered = []
    for (path, path_regex, method, callback) in endpoints:
        # Add only paths to the list that are part of the LMS API
        if (
            path.startswith("/courses/")
        ):
            filtered.append((path, path_regex, method, callback))
    return filtered
