"""
Student and course analytics.

Format and create csv responses
"""

import csv
from django.http import HttpResponse


def create_csv_response(filename, header, datarows):
    """
    Create an HttpResponse with an attached .csv file

    header   e.g. ['Name', 'Email']
    datarows e.g. [['Jim', 'jim@edy.org'], ['Jake', 'jake@edy.org'], ...]
    """
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename={0}'\
        .format(filename)
    csvwriter = csv.writer(
        response,
        dialect='excel',
        quotechar='"',
        quoting=csv.QUOTE_ALL)

    csvwriter.writerow(header)
    for datarow in datarows:
        encoded_row = [unicode(s).encode('utf-8') for s in datarow]
        csvwriter.writerow(encoded_row)
    return response


def format_dictlist(dictlist):
    """
    Convert FROM [
        {
            'label1': 'value-1,1',
            'label2': 'value-1,2',
            'label3': 'value-1,3',
            'label4': 'value-1,4',
        },
        {
            'label1': 'value-2,1',
            'label2': 'value-2,2',
            'label3': 'value-2,3',
            'label4': 'value-2,4',
        }
    ]

    TO {
        'header': ['label1', 'label2', 'label3', 'label4'],
        'datarows': [['value-1,1', 'value-1,2', 'value-1,3', 'value-1,4'],
                     ['value-2,1', 'value-2,2', 'value-2,3', 'value-2,4']]
    }

    Assumes all keys for input dicts are the same.
    """

    if len(dictlist) > 0:
        header = dictlist[0].keys()
    else:
        header = []

    def dict_to_entry(dct):
        """ Convert dictionary to list for a csv row """
        ordered = sorted(dct.items(), key=lambda (k, v): header.index(k))
        vals = [v for (_, v) in ordered]
        return vals

    datarows = map(dict_to_entry, dictlist)

    return {
        'header': header,
        'datarows': datarows,
    }
