from .models import InfoPage
from django import forms
from django.contrib import admin
from tinymce.widgets import AdminTinyMCE
from hvad.admin import TranslatableAdmin
from hvad.forms import TranslatableModelForm

class InfoPageFrom(TranslatableModelForm):
    page = forms.ChoiceField(choices=InfoPage.PAGES)
    text = forms.CharField(widget=AdminTinyMCE(attrs={'cols': 200, 'rows': 30}))

    class Meta:
        model = InfoPage
        fields = ('page', 'site', 'title', 'text')


class AdminInfoPage(TranslatableAdmin):
    list_display = ('page', 'site_display_name', 'all_translations')
    form = InfoPageFrom

    class Media:
        js = ('/static/tiny_mce/tiny_mce_src.js', '/static/tiny_mce/tiny_mce.js')
        css = {'all': ('/static/css/tinymce-studio-content.css', '/static/css/tinymce-studio-content-fonts.css')}

admin.site.register(InfoPage, AdminInfoPage)
