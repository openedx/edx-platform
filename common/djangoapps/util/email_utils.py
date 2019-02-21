from django.conf import settings
from django.core.mail import send_mail

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def send_mail_with_alias(*args, **kwargs):
    """
    change the alia name of the from_email
    eg. Support <triboo@example.com>
    """
    args_list = list(args)
    try:
        email_showname = configuration_helpers.get_value('email_from_showname', settings.DEFAULT_FROM_EMAIL_SHOW_NAME)
        args_list[2] = "{} <{}>".format(email_showname, args_list[2])
    except AttributeError:
        pass
    return send_mail(*args_list, **kwargs)