from datetime import datetime
from django.utils.timezone import utc


def upload_to_path(instance, filename, folder):
    """
    Create and return path where files will be uploaded. This path has specific formation
    i.e. app_label/folder/filename
    :param instance: An instance of the model where the FileField is defined
    :param filename: The filename that was originally given to the file
    :param folder: The specific folder where files will be uploaded
    :return: path to upload files
    """
    return '{app_label}/{folder}/{filename}'.format(
        app_label=instance._meta.app_label,
        filename=filename,
        folder=folder
    )


def pretty_date(time):
    """
    :param time
    :return: datetime object in "time ago" format
    """
    now = datetime.utcnow().replace(tzinfo=utc)
    diff = now - time
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff == 0:
        if second_diff < 10:
            return "JUST NOW"
        if second_diff < 60:
            return str(second_diff) + " SECONDS AGO"
        if second_diff < 120:
            return "1 MINUTE AGO"
        if second_diff < 3600:
            return str(second_diff / 60) + " MINUTES AGO"
        if second_diff < 7200:
            return "1 HOUR AGO"
        if second_diff < 86400:
            return str(second_diff / 3600) + " HOURS AGO"
    if day_diff == 1:
        return "YESTERDAY"
    if day_diff < 7:
        return str(day_diff) + " DAYS AGO"
    if day_diff < 14:
        return "1 WEEK AGO"
    if day_diff < 31:
        return str(day_diff / 7) + " WEEKS AGO"
    if day_diff < 60:
        return "1 MONTH AGO"
    if day_diff < 365:
        return str(day_diff / 30) + " MONTHS AGO"
    if day_diff < 730:
        return "1 YEAR AGO"
    return str(day_diff / 365) + " YEARS AGO"
