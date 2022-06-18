from django.test import TestCase

from waffle import get_waffle_flag_model
from waffle.models import Switch, Sample


class ModelsTests(TestCase):
    def test_natural_keys(self):
        flag = get_waffle_flag_model().objects.create(name='test-flag')
        switch = Switch.objects.create(name='test-switch')
        sample = Sample.objects.create(name='test-sample', percent=0)

        self.assertEqual(flag.natural_key(), ('test-flag',))
        self.assertEqual(switch.natural_key(), ('test-switch',))
        self.assertEqual(sample.natural_key(), ('test-sample',))

        self.assertEqual(get_waffle_flag_model().objects.get_by_natural_key('test-flag'), flag)
        self.assertEqual(Switch.objects.get_by_natural_key('test-switch'), switch)
        self.assertEqual(Sample.objects.get_by_natural_key('test-sample'), sample)

    def test_flag_is_not_active_for_none_requests(self):
        flag = get_waffle_flag_model().objects.create(name='test-flag')
        self.assertEqual(flag.is_active(None), False)