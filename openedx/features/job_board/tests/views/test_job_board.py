from ddt import data, ddt, unpack
from rest_framework import status
from w3lib.url import add_or_replace_parameters

from django.test import TestCase
from django.urls import reverse

from openedx.core.djangolib.testing.philu_utils import configure_philu_theme
from openedx.features.job_board.constants import (
    JOB_COMP_HOURLY_KEY,
    JOB_COMP_SALARIED_KEY,
    JOB_COMP_VOLUNTEER_KEY,
    JOB_HOURS_FREELANCE_KEY,
    JOB_HOURS_FULLTIME_KEY,
    JOB_HOURS_PARTTIME_KEY,
    JOB_PARAM_CITY_KEY,
    JOB_PARAM_COUNTRY_KEY,
    JOB_PARAM_QUERY_KEY,
    JOB_PARAM_TRUE_VALUE,
    JOB_TYPE_ONSITE_KEY,
    JOB_TYPE_REMOTE_KEY
)
from openedx.features.job_board.models import Job
from openedx.features.job_board.tests.factories import JobFactory
from openedx.features.job_board.views import JobCreateView, JobListView


@ddt
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
        self.assertEqual(JobCreateView.form_class.Meta.fields, '__all__')

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

    @unpack
    @data(('', 10), ('?page=2', 4))
    def test_job_list_view_pagination(self, page_query_param, job_list_size):
        # Create multiple new jobs to test pagination.
        JobFactory.create_batch(14)
        response_second_page = self.client.get(reverse('job_list') + page_query_param)
        self.assertEqual(response_second_page.status_code, status.HTTP_200_OK)
        self.assertTrue('is_paginated' in response_second_page.context_data)
        self.assertTrue(response_second_page.context_data['is_paginated'] is True)
        self.assertTrue(len(response_second_page.context_data['job_list']) == job_list_size)

    @data(JOB_TYPE_REMOTE_KEY, JOB_TYPE_ONSITE_KEY)
    def test_job_list_view_filters_job_type(self, job_type):
        # Create a new job with `type=job_type` to search for.
        # And another job with `type="test"` to see it's not fetched.
        JobFactory(type=job_type)
        JobFactory(type="test")

        query_params = {job_type: JOB_PARAM_TRUE_VALUE}
        response = self.client.get(add_or_replace_parameters(reverse('job_list'), query_params))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.context_data['search_fields'][job_type], JOB_PARAM_TRUE_VALUE)

        # ensure that no other filter was applied
        del [response.context_data['search_fields'][job_type]]
        self.assertTrue(not any(response.context_data['search_fields'].values()))

        self.assertTrue(response.context_data['filtered'], True)
        self.assertTrue(len(response.context_data['job_list']) == 1)
        self.assertEqual(response.context_data['job_list'].first().type, job_type)

    @data(JOB_COMP_VOLUNTEER_KEY, JOB_COMP_HOURLY_KEY, JOB_COMP_SALARIED_KEY)
    def test_job_list_view_filters_job_compensation(self, job_comp):
        # Create a new job with `compensation=job_comp` to search for.
        # And another job with `compensation="test"` to see it's not fetched.
        JobFactory(compensation=job_comp)
        JobFactory(compensation="test")

        query_params = {job_comp: JOB_PARAM_TRUE_VALUE}
        response = self.client.get(add_or_replace_parameters(reverse('job_list'), query_params))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.context_data['search_fields'][job_comp], JOB_PARAM_TRUE_VALUE)

        # ensure that no other filter was applied
        del [response.context_data['search_fields'][job_comp]]
        self.assertTrue(not any(response.context_data['search_fields'].values()))

        self.assertTrue(response.context_data['filtered'], True)
        self.assertTrue(len(response.context_data['job_list']) == 1)
        self.assertEqual(response.context_data['job_list'].first().compensation, job_comp)

    @data(JOB_HOURS_FULLTIME_KEY, JOB_HOURS_PARTTIME_KEY, JOB_HOURS_FREELANCE_KEY)
    def test_job_list_view_filters_job_hours(self, job_hours):
        # Create a new job with `hours=job_hours` to search for.
        # And another job with `hours="test"` to see it's not fetched.
        JobFactory(hours=job_hours)
        JobFactory(hours="test")

        query_params = {job_hours: JOB_PARAM_TRUE_VALUE}
        response = self.client.get(add_or_replace_parameters(reverse('job_list'), query_params))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.context_data['search_fields'][job_hours], JOB_PARAM_TRUE_VALUE)

        # ensure that no other filter was applied
        del [response.context_data['search_fields'][job_hours]]
        self.assertTrue(not any(response.context_data['search_fields'].values()))

        self.assertTrue(response.context_data['filtered'], True)
        self.assertTrue(len(response.context_data['job_list']) == 1)
        self.assertEqual(response.context_data['job_list'].first().hours, job_hours)

    def test_job_list_view_filters_job_location(self):
        # Create a new job with custom location to search for.
        job = JobFactory(country='PK', city='Karachi')

        query_params = {JOB_PARAM_CITY_KEY: job.city, JOB_PARAM_COUNTRY_KEY: job.country.name}
        response = self.client.get(add_or_replace_parameters(reverse('job_list'), query_params))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.context_data['search_fields']['country'], job.country.name)
        self.assertTrue(response.context_data['search_fields']['city'], job.city)

        # ensure that no other filter was applied
        del [response.context_data['search_fields']['country']]
        del [response.context_data['search_fields']['city']]
        self.assertTrue(not any(response.context_data['search_fields'].values()))

        self.assertTrue(response.context_data['filtered'], True)
        self.assertTrue(len(response.context_data['job_list']) == 1)
        self.assertTrue(response.context_data['job_list'][0].country.name == job.country.name)
        self.assertTrue(response.context_data['job_list'][0].city == job.city)

    def test_job_list_view_filters_job_query(self):
        # Create a new job with custom title to search for.
        job = JobFactory(title='custom_job')

        query_params = {JOB_PARAM_QUERY_KEY: job.title}
        response = self.client.get(add_or_replace_parameters(reverse('job_list'), query_params))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.context_data['search_fields']['query'], job.title)

        # ensure that no other filter was applied
        del [response.context_data['search_fields']['query']]
        self.assertTrue(not any(response.context_data['search_fields'].values()))

        self.assertTrue(response.context_data['filtered'], True)
        self.assertTrue(len(response.context_data['job_list']) == 1)
        self.assertTrue(job.title in response.context_data['job_list'][0].title)
