from django.utils.translation import ugettext as _, override
from django.utils.formats import dateformat, get_format


def translate_date(date, language, date_format='DATE_FORMAT'):
    """
    Converts the provided date object into a string, while translating
    its value for the given language.  Both the format of the date
    as well as its values (i.e., name of the Month) are translated.

    For example:
        date = datetime.datetime(2017, 12, 23)
        date_in_spanish = translate_date(date, 'es')
        assert date_in_spanish = '12 de Deciembre de 2017'
    """
    with override(language):
        return dateformat.format(
            date,
            get_format(date_format, lang=language, use_l10n=True),
        )
