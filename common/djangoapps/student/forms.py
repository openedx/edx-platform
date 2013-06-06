from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth.hashers import UNUSABLE_PASSWORD, is_password_usable, get_hasher
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.utils.http import int_to_base36



# This is a literal copy from Django 1.4.5's django.contrib.auth.forms.PasswordResetForm
# I think copy-and-paste here is somewhat better than subclassing and
# just changing the definition of clean_email, because it's less
# likely to be broken by incompatibility with a new django version.
# (If this form is good enough now, a snapshot of it ought to last a while)

class PasswordResetFormNoActive(forms.Form):
    error_messages = {
        'unknown': _("That e-mail address doesn't have an associated "
                     "user account. Are you sure you've registered?"),
        'unusable': _("The user account associated with this e-mail "
                      "address cannot reset the password."),
    }
    email = forms.EmailField(label=_("E-mail"), max_length=75)
    
    def clean_email(self):
        """
            Validates that an active user exists with the given email address.
            """
        email = self.cleaned_data["email"]
        #The line below contains the only change, removing is_active=True
        self.users_cache = User.objects.filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if any((user.password == UNUSABLE_PASSWORD)
               for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email
    
    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
            Generates a one-use only link for resetting password and sends to the
            user.
            """
        from django.core.mail import send_mail
        for user in self.users_cache:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
            send_mail(subject, email, from_email, [user.email])

