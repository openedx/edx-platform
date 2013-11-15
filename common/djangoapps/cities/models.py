from django.db import models
from django.utils.translation import ugettext as _

class City(models.Model):
    name = models.CharField(max_length=64, verbose_name=_('City'))
    code = models.CharField(max_length=64, verbose_name=_('Code'))

    class Meta:
        verbose_name_plural = _('Cities')
    
