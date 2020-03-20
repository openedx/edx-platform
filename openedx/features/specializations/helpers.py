from datetime import datetime


def date_from_str(date_str, date_format='%Y-%m-%dT%H:%M:%SZ'):
    return datetime.strptime(date_str, date_format)
