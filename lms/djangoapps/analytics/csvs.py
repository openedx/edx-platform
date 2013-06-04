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
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
    csvwriter = csv.writer(response, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
    csvwriter.writerow(header)
    for datarow in datarows:
        encoded_row = [unicode(s).encode('utf-8') for s in datarow]
        csvwriter.writerow(encoded_row)
    return response


def format_dictlist(dictlist):
    """
    Convert from [
        {
            'label1': 'value1,1',
            'label2': 'value2,1',
            'label3': 'value3,1',
            'label4': 'value4,1',
        },
        {
            'label1': 'value1,2',
            'label2': 'value2,2',
            'label3': 'value3,2',
            'label4': 'value4,2',
        }
    ]

    to {
        'header': ['label1', 'label2', 'label3', 'label4'],
        'datarows': ['value1,1', 'value2,1', 'value3,1', 'value4,1'], ['value1,2', 'value2,2', 'value3,2', 'value4,2']
    }

    Do not handle empty lists.
    """

    header = dictlist[0].keys()

    def dict_to_entry(d):
        ordered = sorted(d.items(), key=lambda (k, v): header.index(k))
        vals = map(lambda (k, v): v, ordered)
        return vals

    datarows = map(dict_to_entry, dictlist)

    return {
        'header':   header,
        'datarows': datarows,
    }
