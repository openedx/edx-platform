"""
A series of sorting functions to help sort search results
"""


def sort(data_list, sorting):
    """
    General sort handler, used by SearchResults model for search sorting
    """

    if sorting == "alphabetical":
        return alphabetical_sort(data_list)
    elif sorting == "relevance":
        return relevance_sort(data_list)
    else:
        return data_list


def relevance_sort(data_list):
    """
    Sorts items in data_list according to a score attribute of each item in data_list
    """

    sorting = lambda entry: entry.score
    ascending = sorted(data_list, key=sorting, reverse=True)
    return ascending


def alphabetical_sort(data_list):
    """
    Sorts items in data_list alphabetically by display_name in the data field of each object
    """

    sorting = lambda entry: entry.data.get("display_name", "").lower()
    return sorted(data_list, key=sorting)
