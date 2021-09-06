from django.db import models

from oauth2_provider.models import Application


class TrustedApplication(models.Model):
    """Identify that an OAuth2 application is a trusted application.

    This exists to replace behavior that existed in Hawthorn but apparently
    removed in subsequent releases. The model class that existed in Hawthorn was
    `edx_oauth2_provider.models.TrustedClient`. Since the actors in the
    participating Python OAuth2 packages changed from 'Client' to 'Application',
    we name this class `TrustedApplication` instead of `TrustedClient`.

    This functionality _might_ exist in Juniper. However it is not clear, we
    have our own customizations for auth, so adding this model let's us reuse
    some of the same mechanisms to prevent trusted application.

    We could extend Application to add a 'trusted bit' to it and this might be
    a good idea in the future. For now we're implementing this as a distinct
    model to make it easier to debug and troubleshoot
    """
    application = models.OneToOneField(Application, on_delete=models.CASCADE)

    def __str__(self):
        return 'TrustedClient[{pk}] for {application}'.format(
            pk=self.id,
            application=self.application)
