from datetime import timedelta


def get_next_date(today, module_date):
    return str(today + timedelta(days=module_date))
