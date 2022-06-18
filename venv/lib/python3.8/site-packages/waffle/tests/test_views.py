from django.urls import reverse

from waffle import get_waffle_flag_model
from waffle.models import Sample, Switch
from waffle.tests.base import TestCase


class WaffleViewTests(TestCase):
    def test_wafflejs(self):
        response = self.client.get(reverse('wafflejs'))
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/x-javascript', response['content-type'])
        cache_control = [control.strip()
                         for control in response['cache-control'].split(',')]
        self.assertIn('max-age=0', cache_control)

    def test_flush_all_flags(self):
        """Test the 'FLAGS_ALL' list gets invalidated correctly."""
        get_waffle_flag_model().objects.create(name='myflag1', everyone=True)
        response = self.client.get(reverse('wafflejs'))
        self.assertEqual(200, response.status_code)
        assert ('myflag1', True) in response.context['flags']

        get_waffle_flag_model().objects.create(name='myflag2', everyone=True)
        response = self.client.get(reverse('wafflejs'))
        self.assertEqual(200, response.status_code)
        assert ('myflag2', True) in response.context['flags']

    def test_flush_all_switches(self):
        """Test the 'SWITCHES_ALL' list gets invalidated correctly."""
        switch = Switch.objects.create(name='myswitch', active=True)
        response = self.client.get(reverse('wafflejs'))
        self.assertEqual(200, response.status_code)
        assert ('myswitch', True) in response.context['switches']

        switch.active = False
        switch.save()
        response = self.client.get(reverse('wafflejs'))
        self.assertEqual(200, response.status_code)
        assert ('myswitch', False) in response.context['switches']

    def test_flush_all_samples(self):
        """Test the 'SAMPLES_ALL' list gets invalidated correctly."""
        Sample.objects.create(name='sample1', percent='100.0')
        response = self.client.get(reverse('wafflejs'))
        self.assertEqual(200, response.status_code)
        assert ('sample1', True) in response.context['samples']

        Sample.objects.create(name='sample2', percent='100.0')

        response = self.client.get(reverse('wafflejs'))
        self.assertEqual(200, response.status_code)
        assert ('sample2', True) in response.context['samples']
