def sort(data_list, sorting):
    if sorting == "alphabetical":
        return alphabetical_sort(data_list)
    elif sorting == "relevance":
        return relevance_sort(data_list)
    else:
        return data_list


def relevance_sort(data_list):
    sorting = lambda entry: entry.data.get("score", 0)
    ascending = sorted(data_list, key=sorting)
    ascending.reverse()  # Now descending
    return ascending


def alphabetical_sort(data_list):
    sorting = lambda entry: " ".join(entry.data.get("display_name", "")).lower()
    return sorted(data_list, key=sorting)
