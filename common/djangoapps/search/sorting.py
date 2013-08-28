"""
A series of sorting functions to help sort search results
"""

SORTING_DICT = {
    "relevance": [lambda entry: entry.score, True],
    "alphabetical": [lambda entry: entry.data.get("display_name", "").lower(), False]
}


def sort(data_list, sorting):
    """
    General sort handler, used by SearchResults model for search sorting
    """

    return sorted(data_list, key=SORTING_DICT[sorting][0], reverse=SORTING_DICT[sorting][1])
