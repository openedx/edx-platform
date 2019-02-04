from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from hvad.models import TranslatableModel, TranslatedFields


def get_pages():
    pages = []

    for key, value in settings.MKTG_URL_LINK_MAP.items():
        if value is None or key == "ROOT" or key == "COURSES":
            continue

        template = "%s.html" % key.lower()

        pages.append((template, value))

    return tuple(pages)


class InfoPage(TranslatableModel):
    PAGES = get_pages()

    page = models.CharField(max_length=50, choices=PAGES, unique=True)
    translations = TranslatedFields(
        title = models.CharField(max_length=255),
        text = models.TextField()
    )
    site = models.ForeignKey(
        Site,
        default=settings.SITE_ID,
        related_name='%(class)ss',
        help_text=_(
            'The Site that this provider configuration belongs to.'
        ),
        on_delete=models.CASCADE,
    )

    def __unicode__(self):
        return self.page

    def site_display_name(self):
        return self.site and self.site.name or None
