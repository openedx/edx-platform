from datetime import datetime

DISCOVERY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def date_from_str(date_str, date_format=DISCOVERY_DATE_FORMAT):
    return datetime.strptime(date_str, date_format)
