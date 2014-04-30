
import ConfigParser
from django.conf import settings

config_file = open(settings.REPO_ROOT / "docs" / "config.ini")
config = ConfigParser.ConfigParser()
config.readfp(config_file)


def doc_url(request):
    # in the future, we will detect the locale; for now, we will
    # hardcode en_us, since we only have English documentation
    locale = "en_us"

    def get_doc_url(token):
        try:
            return config.get(locale, token)
        except ConfigParser.NoOptionError:
            return config.get(locale, "default")

    return {"doc_url": get_doc_url}
