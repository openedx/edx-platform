"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from cities.models import State, City


class SimpleTest(TestCase):

    def setUp(self):
        self.state = State.objects.create(code='101', name='Azuay', country='EC')
        self.city = City.objects.create(code='01', name='Cuenca', state=self.state)
    
    def test_create_model_state(self):
        self.assertEqual(self.state.name, 'Azuay')
        self.assertEqual(self.city.name, 'Cuenca')
        self.assertEqual(self.city.state.country.code, 'EC')
        
