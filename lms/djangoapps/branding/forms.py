from django import forms
from django.utils.translation import ugettext as _


class ContactForm(forms.Form):
    name = forms.CharField(label=_('Name'), max_length=255)
    email = forms.EmailField(label=_('E-mail'), max_length=255)
    phone = forms.CharField(label=_('Mobile phone number'), max_length=16, required=False)
    message = forms.CharField(label=_('Message:'), widget=forms.Textarea)

    @property
    def get_data(self):
        base_result = self.cleaned_data
        return base_result

    def as_ul_with_class(self, css_classes):
        """
        Return this form rendered as HTML <li class=''>s -- excluding the <ul></ul>.
        """
        return self._html_output(
            normal_row=(
                '<li class="{css_classes}">%(errors)s%(label)s %(field)s%(help_text)s</li>'.
                format(css_classes=css_classes)
            ),
            error_row='<li>%s</li>',
            row_ender='</li>',
            help_text_html='<span class="helptext">%s</span>',
            errors_on_separate_row=False,
        )

    def save(self):
        raise NotImplementedError
