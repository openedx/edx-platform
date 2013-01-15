from django.test import TestCase 
from courseware import progress
from mock import MagicMock



class ProgessTests(TestCase):
	def setUp(self):

		self.d = dict({'duration_total': 0,
		     'duration_watched': 0,
		     'done': True,
		     'questions_correct': 4,
		     'questions_incorrect': 0,
		     'questions_total': 0})

		self.c = progress.completion()
		self.c2= progress.completion()
		self.c2.dict = dict({'duration_total': 0,
		     'duration_watched': 0,
		     'done': True,
		     'questions_correct': 2,
		     'questions_incorrect': 1,
		     'questions_total': 0})

		self.cplusc2 = dict({'duration_total': 0,
		     'duration_watched': 0,
		     'done': True,
		     'questions_correct': 2,
		     'questions_incorrect': 1,
		     'questions_total': 0})

		

		self.oth = dict({'duration_total': 0,
		     'duration_watched': 0,
		     'done': True,
		     'questions_correct': 4,
		     'questions_incorrect': 0,
		     'questions_total': 7})

		self.x = MagicMock()
		self.x.dict = self.oth

		self.d_oth = {'duration_total': 0,
	     'duration_watched': 0,
	     'done': True,
	     'questions_correct': 4,
	     'questions_incorrect': 0,
	     'questions_total': 7}
	def test_getitem(self):
		self.assertEqual(self.c.__getitem__('duration_watched'), 0)

	def test_setitem(self):
		self.c.__setitem__('questions_correct', 4)
		self.assertEqual(str(self.c),str(self.d))

	# def test_add(self):
	# 	self.assertEqual(self.c.__add__(self.c2), self.cplusc2)

	def test_contains(self):

		return self.c.__contains__('meow')
		#self.assertEqual(self.c.__contains__('done'), True)

	def test_repr(self):
		self.assertEqual(self.c.__repr__(), str(progress.completion()))
