from constants import CREDENTIALS_DATE_FORMAT
from datetime import datetime


def date_from_str(date_str, date_format=CREDENTIALS_DATE_FORMAT):
    return datetime.strptime(date_str, date_format)


def extract_utm_params(input_dict):
    """
    This method returns a subset of the input dictionary that only contains the utm params found
    in the input_dict
    :param input_dict: a dictionary that may or may not contain utm parameters
    :return: a dictionary containing only utm_params found in the utm_keys
    """
    if not input_dict:
        return dict()

    utm_keys = [
        'utm_source',
        'utm_medium',
        'utm_campaign',
        'utm_content',
        'utm_term'
    ]

    return {key: value for key, value in input_dict.items() if key in utm_keys}
