"""
Factories for tests of Programs.
"""


# pylint: disable=missing-docstring,unnecessary-lambda
import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from openedx.core.djangoapps.credentials_service import models
import factory
from django.core.files.base import ContentFile
from factory.django import DjangoModelFactory, ImageField
from factory.fuzzy import FuzzyText
from openedx.core.djangoapps.credentials_service.models import ProgramCertificate


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = Site

    domain = factory.Sequence(u'domain{0}.com'.format)
    name = factory.Sequence(u'name{0}'.format)


class SiteConfigurationFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.SiteConfiguration

    site = factory.SubFactory(SiteFactory)
    lms_url_root = factory.Sequence(u'http://domain{0}.com'.format)
    theme_scss_path = FuzzyText('foo')


class CertificateTemplateFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.CertificateTemplate
    name = FuzzyText('Home Template')
    content = FuzzyText('foo')


class SignatoryFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.Signatory

    name = FuzzyText('foo')
    title = FuzzyText('bar')
    image = factory.LazyAttribute(
        lambda _: ContentFile(
            ImageField()._make_data(  # pylint: disable=protected-access
            {'color': 'blue', 'width': 50, 'height': 50, 'format': 'PNG'}
            ), 'test.png'
        )
    )


class AbstractCredentialFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.AbstractCredential
        abstract = True

    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.save()
        return obj

class AbstractCertificateFactory(AbstractCredentialFactory):
    class Meta(object):
        model = models.AbstractCertificate
        abstract = True

    # signatories = factory.SubFactory(SignatoryFactory)
    # template = factory.SubFactory(CertificateTemplateFactory)
    # title = FuzzyText('Audit Certificate')


class ProgramCertificateFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.ProgramCertificate

    program_id = factory.Sequence(lambda n: n)
    site = factory.SubFactory(SiteFactory)
    template = factory.SubFactory(CertificateTemplateFactory)
    title = FuzzyText('programs title')

    @factory.post_generation
    def post(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        sign = SignatoryFactory.create()
        self.signatories.add(sign)


class UserCredentialFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.UserCredential

    credential_object = factory.SubFactory(ProgramCertificateFactory)
    username = FuzzyText('Home Template')
    status = 'awarded'
    download_url = 'aa'
    uuid = factory.LazyAttribute(lambda o: uuid.uuid4().hex)  # pylint: disable=undefined-variable



class UserCredentialAttributeFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = models.UserCredentialAttribute

    user_credential = factory.SubFactory(UserCredentialFactory)
    namespace = 'name space'
    name = 'testing name'
    value = 'testing value'
