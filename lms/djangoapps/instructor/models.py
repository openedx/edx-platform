from config_models.models import ConfigurationModel
from django.contrib.sites.models import Site
from django.db.models import ForeignKey, CharField

class CommunicatorConfig(ConfigurationModel):
    class Meta(object):
        app_label = 'instructor'

    KEY_FIELDS = ('site', 'course')

    site = ForeignKey(Site)
    course = CharField(max_length=512)

    # max_length in Edge and IE is 2047
    # https://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers
    backend_url = CharField(max_length=2048)
