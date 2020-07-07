import factory

from student.tests.factories import UserFactory as ParentUserFactory
from factory.django import DjangoModelFactory

from ..models import UserExtendedProfile, Organization, EmailPreference


class UserFactory(ParentUserFactory):

    @factory.post_generation
    def extended_profile(self, create, extracted, **kwargs):
        if create:
            self.save()
            return UserExtendedProfileFactory.create(user=self, **kwargs)
        elif kwargs:
            raise Exception("Cannot build a user extended profile without saving the user")
        else:
            return None

    @factory.post_generation
    def email_preferences(self, create, extracted, **kwargs):
        if create:
            self.save()
            return EmailPreferenceFactory.create(user=self, **kwargs)
        elif kwargs:
            raise Exception("Cannot build a email preferences without saving the user")
        else:
            return None


class UserExtendedProfileFactory(DjangoModelFactory):
    class Meta(object):
        model = UserExtendedProfile
        django_get_or_create = ('user', )

    user = None
    is_interests_data_submitted = True


class EmailPreferenceFactory(DjangoModelFactory):
    class Meta(object):
        model = EmailPreference
        django_get_or_create = ('user', )

    user = None
    opt_in = 'no'


class OrganizationFactory(DjangoModelFactory):
    class Meta(object):
        model = Organization
        django_get_or_create = ('label', )

    label = factory.Sequence(u'Organization{0}'.format)
    org_type = factory.Faker('pystr', max_chars=10)
