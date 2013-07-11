def sort(data_list, sorting):
    if sorting == "alphabetical":
        return alphabetical_sort(data_list)
    elif sorting == "relevance":
        return relevance_sort(data_list)
    else:
        return data_list


def relevance_sort(data_list):
    sorting = lambda entry: entry[4]
    return sorted(data_list, key=sorting)


def alphabetical_sort(data_list):
    sorting = lambda entry: " ".join(entry[0].split()[2:]).lower()
    return sorted(data_list, key=sorting)
