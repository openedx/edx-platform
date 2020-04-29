from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from openedx.core.djangolib.testing.philu_utils import configure_philu_theme
from openedx.features.job_board.models import Job
from openedx.features.job_board.tests.factories import JobFactory
from openedx.features.job_board.views import JobCreateView, JobListView


class JobBoardViewTest(TestCase):

    def setUp(self):
        self.client.logout()

    @classmethod
    def setUpClass(cls):
        super(JobBoardViewTest, cls).setUpClass()
        configure_philu_theme()

    def test_job_create_view(self):
        response = self.client.get(reverse('job_create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(JobCreateView.fields, '__all__')

    def test_create_view_post_successful(self):
        self.client.post('/jobs/create/', {"function": "dummy function",
                                           "city": "Lahore",
                                           "description": "dummy description",
                                           "title": "second title",
                                           "country": "AX",
                                           "company": "dummy company",
                                           "responsibilities": "dummy responsibilities",
                                           "hours": "parttime",
                                           "compensation": "salaried",
                                           "contact_email": "test@test.com",
                                           "logo": "",
                                           "type": "remote",
                                           "website_link": ""})
        self.assertEqual(Job.objects.all().count(), 1)

    def test_create_view_post_unsuccessful(self):
        self.client.post('/jobs/create/', {"function": "dummy function",
                                           "city": "Lahore",
                                           "description": "dummy description",
                                           "title": "second title",
                                           "country": "AX",
                                           "company": "dummy company",
                                           "responsibilities": "dummy responsibilities",
                                           "hours": "parttime",
                                           "compensation": "salaried",
                                           "contact_email": "test", #incorrect email
                                           "logo": "",
                                           "type": "remote",
                                           "website_link": ""})
        self.assertEqual(Job.objects.all().count(), 0)

    def test_job_detail_view_invalid_pk(self):
        response = self.client.get(reverse('job_detail', kwargs={'pk': 1}), follow=True)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_job_detail_view_valid_pk(self):
        job = JobFactory()
        response = self.client.get(reverse('job_detail', kwargs={'pk': job.id}), follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_job_list_view(self):
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(JobListView.paginate_by, 10)
        self.assertEqual(JobListView.ordering, ['-created'])
