"""
This test file will run through some XBlock test scenarios regarding the recommender system
"""
import json
import tempfile
import itertools
from copy import deepcopy

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from courseware.tests.factories import GlobalStaffFactory

from lms.lib.xblock.runtime import quote_slashes


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestRecommender(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Check that Recommender state is saved properly.
    """
    STUDENT_INFO = [('view@test.com', 'foo'), ('view2@test.com', 'foo')]

    def setUp(self):
        self.course = CourseFactory.create(
            display_name='Recommender_Test_Course')
        self.chapter = ItemFactory.create(parent=self.course,
                                          display_name='Overview')
        self.section = ItemFactory.create(parent=self.chapter,
                                          display_name='Welcome')
        self.unit = ItemFactory.create(parent=self.section,
                                       display_name='New Unit')
        self.xblock = ItemFactory.create(parent=self.unit,
                                         category='recommender',
                                         display_name='recommender')
        self.xblock2 = ItemFactory.create(parent=self.unit,
                                          category='recommender',
                                          display_name='recommender_second')

        self.xblock_names = ['recommender', 'recommender_second']

        self.test_recommendations = [
            {
                "title": "Covalent bonding and periodic trends",
                "url": "https://courses.edx.org/courses/MITx/3.091X/" +
                "2013_Fall/courseware/SP13_Week_4/" +
                "SP13_Periodic_Trends_and_Bonding/",
                "description": "http://people.csail.mit.edu/swli/edx/" +
                "recommendation/img/videopage1.png",
                "descriptionText": "short description for Covalent bonding " +
                "and periodic trends"
            },
            {
                "title": "Polar covalent bonds and electronegativity",
                "url": "https://courses.edx.org/courses/MITx/3.091X/" +
                "2013_Fall/courseware/SP13_Week_4/SP13_Covalent_Bonding/",
                "description": "http://people.csail.mit.edu/swli/edx/" +
                "recommendation/img/videopage2.png",
                "descriptionText": "short description for Polar covalent " +
                "bonds and electronegativity"
            }
        ]

        # Create student accounts and activate them.
        for i, (email, password) in enumerate(self.STUDENT_INFO):
            username = "u{}".format(i)
            self.create_account(username, email, password)
            self.activate_user(email)

        self.staff_user = GlobalStaffFactory()

    def get_handler_url(self, handler, xblock_name='recommender'):
        """
        Get url for the specified xblock handler
        """
        return reverse('xblock_handler', kwargs={
            'course_id': self.course.id.to_deprecated_string(),
            'usage_id': quote_slashes(self.course.id.make_usage_key('recommender', xblock_name).to_deprecated_string()),
            'handler': handler,
            'suffix': ''
        })

    def enroll_student(self, email, password):
        """
        Student login and enroll for the course
        """
        self.login(email, password)
        self.enroll(self.course, verify=True)

    def enroll_staff(self, email):
        """
        Staff login and enroll for the course
        """
        password = 'test'
        self.login(email, password)
        self.enroll(self.course, verify=True)

    def add_resource(self, resource, xblock_name='recommender'):
        """
        Add resource to RecommenderXBlock
        """
        url = self.get_handler_url('add_resource', xblock_name)
        resp = self.client.post(url, json.dumps(resource), '')
        return json.loads(resp.content)

    def check_for_get_xblock_page_code(self, code):
        """
        Check the response.status_code for getting the page where the XBlock attached
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'chapter': 'Overview',
                'section': 'Welcome',
            }
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, code)

    def check_ajax_event_result(self, data, handler, expected_result, xblock_name='recommender'):
        """
        Check whether the return of ajax event is the same as expected
        """
        url = self.get_handler_url(handler, xblock_name)
        resp = self.client.post(url, json.dumps(data), '')
        result = json.loads(resp.content)
        self.assertDictEqual(result, expected_result)
        self.check_for_get_xblock_page_code(200)

    def test_endorse_resource(self):
        """
        Verify that the endorsement of an entry is successful
        """
        self.enroll_student(self.STUDENT_INFO[0][0], self.STUDENT_INFO[0][1])
        # Add resources, assume correct here, tested in test_add_resource
        for resource in self.test_recommendations:
            for xblock_name in self.xblock_names:
                self.add_resource(resource, xblock_name)

        test_cases = [
            [
                {
                    'expected_result': {
                        'Success': False,
                        'error': 'Endorse resource without permission'
                    },
                    'data': {'id': 0}
                }
            ],  # Students have no right to endorse an entry
            [
                {
                    'expected_result': {
                        'Success': False,
                        'error': 'bad id',
                        'id': 100
                    },
                    'data': {'id': 100}  # Endorse a non-existing entry
                },
                {
                    'expected_result': {
                        'Success': True,
                        'status': 'endorsement',
                        'id': 1
                    },
                    'data': {'id': 1}  # Endorse an entry
                },
                {
                    'expected_result': {
                        'Success': True,
                        'status': 'undo endorsement',
                        'id': 1
                    },
                    'data': {'id': 1}  # Un-endorse an entry
                },
                {
                    'expected_result': {
                        'Success': True,
                        'status': 'endorsement',
                        'id': 1
                    },
                    'data': {'id': 1}  # Endorse an entry
                },
                {
                    'expected_result': {
                        'Success': True,
                        'status': 'endorsement',
                        'id': 0
                    },
                    'data': {'id': 0}  # Endorse a diffenent entry
                }
            ]  # Staff has the right to endorse an entry
        ]

        for index in range(0, len(test_cases)):
            for test_case, xblock_name in itertools.product(test_cases[index],
                                                            self.xblock_names):
                self.check_ajax_event_result(test_case['data'],
                                             'endorse_resource',
                                             test_case['expected_result'],
                                             xblock_name)  # Test whether the two blocks affect each other
            if index == 0:
                self.logout()
                self.enroll_staff(self.staff_user.email)

    def test_delete_resource(self):
        """
        Verify that the deletion of an entry is successful
        """
        self.enroll_student(self.STUDENT_INFO[0][0], self.STUDENT_INFO[0][1])
        # Add resources, assume correct here, tested in test_add_resource
        for resource in self.test_recommendations:
            for xblock_name in self.xblock_names:
                self.add_resource(resource, xblock_name)

        test_cases = [
            [
                {
                    'expected_result': {
                        'Success': False,
                        'error': 'Delete resource without permission'
                    },
                    'data': {'id': 0}
                }
            ],  # Students have no right to delete an entry
            [
                {
                    'expected_result': {
                        'Success': False,
                        'error': 'bad id',
                        'id': 100
                    },
                    'data': {'id': 100}  # Delete a non-existing entry
                },
                {
                    'expected_result': {
                        'Success': True,
                        'upvotes': 0,
                        'downvotes': 0,
                        'id': 1
                    },
                    'data': {'id': 1}  # Delete an entry
                },
                {
                    'expected_result': {
                        'Success': False,
                        'error': 'bad id',
                        'id': 1
                    },
                    'data': {'id': 1}  # Delete an previously removed (thus, non-existing) entry
                }
            ]  # Staff has the right to delete an entry
        ]
        for field in self.test_recommendations[1]:
            test_cases[1][1]['expected_result'][field] = self.test_recommendations[1][field]

        for index in range(0, len(test_cases)):
            for test_case, xblock_name in itertools.product(test_cases[index],
                                                            self.xblock_names):
                self.check_ajax_event_result(test_case['data'],
                                             'delete_resource',
                                             test_case['expected_result'],
                                             xblock_name)  # Test whether the two blocks affect each other
            if index == 0:
                self.logout()
                self.enroll_staff(self.staff_user.email)

    def test_handle_vote(self):
        """
        Verify the voting is handled correctly
        """
        self.enroll_staff(self.staff_user.email)
        # Add resources, assume correct here, tested in test_add_resource
        for resource in self.test_recommendations:
            for xblock_name in self.xblock_names:
                self.add_resource(resource, xblock_name)

        test_cases = [
            [
                {
                    'expected_result': {
                        'Success': False,
                        'error': 'bad id',
                        'id': 100
                    },
                    'handler': 'handle_upvote',
                    'data': {'id': 100}  # Check upvoting resources with non-existing id fails
                },
                {
                    'expected_result': {
                        'Success': False,
                        'error': 'bad id',
                        'id': 100
                    },
                    'handler': 'handle_downvote',
                    'data': {'id': 100}  # Check downvoting resources with non-existing id fails
                },
                {
                    'expected_result': {
                        'Success': True,
                        'oldVotes': 0,
                        'newVotes': 1,
                        'id': 0
                    },
                    'handler': 'handle_upvote',
                    'data': {'id': 0}  # Check whether upvoting success
                },
                {
                    'expected_result': {
                        'Success': True,
                        'oldVotes': 0,
                        'newVotes': -1,
                        'id': 1
                    },
                    'handler': 'handle_downvote',
                    'data': {'id': 1}  # Check whether downvoting success
                }
            ],  # change user
            [
                {
                    'expected_result': {
                        'Success': True,
                        'oldVotes': 1,
                        'newVotes': 2,
                        'id': 0
                    },
                    'handler': 'handle_upvote',
                    'data': {'id': 0}  # check whether we can upvote twice with different accounts
                },
                {
                    'expected_result': {
                        'Success': True,
                        'oldVotes': -1,
                        'newVotes': -2,
                        'id': 1
                    },
                    'handler': 'handle_downvote',
                    'data': {'id': 1}  # check whether we can downvote twice with different accounts
                },
                {
                    'expected_result': {
                        'Success': True,
                        'oldVotes': 2,
                        'newVotes': 0,
                        'toggle': True,
                        'id': 0
                    },
                    'handler': 'handle_downvote',
                    'data': {'id': 0}  # Check whether we can switch upvoting to downvoting
                },
                {
                    'expected_result': {
                        'Success': True,
                        'oldVotes': -2,
                        'newVotes': 0,
                        'toggle': True,
                        'id': 1
                    },
                    'handler': 'handle_upvote',
                    'data': {'id': 1}  # Check whether we can switch downvoting to upvoting
                },
                {
                    'expected_result': {
                        'Success': True,
                        'oldVotes': 0,
                        'newVotes': 1,
                        'id': 0
                    },
                    'handler': 'handle_downvote',
                    'data': {'id': 0}  # Check whether we can cancel downvoting by vote twice (with the same account)
                },
                {
                    'expected_result': {
                        'Success': True,
                        'oldVotes': 0,
                        'newVotes': -1,
                        'id': 1
                    },
                    'handler': 'handle_upvote',
                    'data': {'id': 1}  # Check whether we can cancel upvoting by vote twice (with the same account)
                },
            ]
        ]
        for test_cases_list, student in zip(test_cases, self.STUDENT_INFO):
            # Change user
            self.logout()
            self.enroll_student(student[0], student[1])
            for test_case, xblock_name in itertools.product(test_cases_list,
                                                            self.xblock_names):
                self.check_ajax_event_result(test_case['data'],
                                             test_case['handler'],
                                             test_case['expected_result'],
                                             xblock_name)

    def test_add_resource(self):
        """
        Verify the addition of new resource is handled correctly
        """
        self.enroll_student(self.STUDENT_INFO[0][0], self.STUDENT_INFO[0][1])
        # Check whether adding new resource is successful
        for index, resource in enumerate(self.test_recommendations):
            for xblock_name in self.xblock_names:
                result = self.add_resource(resource, xblock_name)

                expected_result = {
                    'Success': True,
                    'upvotes': 0,
                    'downvotes': 0,
                    'id': index
                }
                for field in resource:
                    expected_result[field] = resource[field]

                self.assertDictEqual(result, expected_result)
                self.check_for_get_xblock_page_code(200)

        # Check whether adding redundant resource (url) is rejected
        url_suffixes = ['', '#IAmSuffix', '%23IAmSuffix']
        for suffix, xblock_name in itertools.product(url_suffixes,
                                                     self.xblock_names):
            resource = deepcopy(self.test_recommendations[0])
            resource['url'] += suffix
            result = self.add_resource(resource, xblock_name)

            expected_result = {
                'Success': False,
                'error': 'redundant resource',
                'dup_id': 0
            }
            for field in resource:
                expected_result[field] = resource[field]
                expected_result['dup_' + field] = self.test_recommendations[0][field]

            self.assertDictEqual(result, expected_result)
            self.check_for_get_xblock_page_code(200)

    def test_edit_resource(self):
        """
        Verify the edition of a existing resource is handled correctly
        """
        self.enroll_student(self.STUDENT_INFO[0][0], self.STUDENT_INFO[0][1])
        # Add resources, assume correct here, tested in test_add_resource
        for resource, xblock_name in itertools.product(self.test_recommendations,
                                                       self.xblock_names):
            self.add_resource(resource, xblock_name)

        # Data for reset
        original_data = {"id": 0}
        original_data.update(self.test_recommendations[0])

        # Check whether editing a resource with non-existing id fails
        data = {"id": 100}
        edited_recommendations = {key: value + " edited" for key, value in self.test_recommendations[0].iteritems()}
        data.update(edited_recommendations)

        test_cases = []
        test_case = {
            'data': deepcopy(data),
            'expected_result': {
                'Success': False,
                'error': 'bad id',
                'id': 100
            }
        }
        test_cases.append(test_case)

        data['id'] = 0
        # Check whether changing the url to the one of 'another' resource is rejected
        url_suffixes = ['', '#IAmSuffix', '%23IAmSuffix']
        for suffix in url_suffixes:
            test_case = {
                'data': deepcopy(data),
                'expected_result': {
                    'Success': False,
                    'error': 'existing url',
                    'id': data['id'],
                    'dup_id': 1
                }
            }
            test_case['data']['url'] = self.test_recommendations[1]['url'] + suffix

            for field in self.test_recommendations[0]:
                test_case['expected_result'][field] = test_case['data'][field]
                test_case['expected_result']['old_' + field] = self.test_recommendations[0][field]
                test_case['expected_result']['dup_' + field] = self.test_recommendations[1][field]

            test_cases.append(test_case)

        # Check whether changing the content of resource is successful
        test_case = {
            'data': deepcopy(data),
            'expected_result': {
                'Success': True,
                'id': data['id'],
            }
        }
        for field in self.test_recommendations[0]:
            test_case['expected_result'][field] = test_case['data'][field]
            test_case['expected_result']['old_' + field] = self.test_recommendations[0][field]

        test_cases.append(test_case)

        # Check whether changing the content of resource is successful,
        # when the provided information is incomplete, or the a varying url to the same page
        expected_result_temp = deepcopy(test_case['expected_result'])
        fixed_field = ['title', 'description', 'descriptionText']
        for index in range(0, len(fixed_field)):
            test_case = {
                'data': deepcopy(data),
                'expected_result': deepcopy(expected_result_temp)
            }
            test_case['data'][fixed_field[index]] = ''
            test_case['data']['url'] = self.test_recommendations[0]['url'] + url_suffixes[index]

            test_case['expected_result']['url'] = test_case['data']['url']
            test_case['expected_result'][fixed_field[index]] = expected_result_temp['old_' + fixed_field[index]]

            test_cases.append(test_case)

        for test_case, xblock_name in itertools.product(test_cases,
                                                        self.xblock_names):
            self.check_ajax_event_result(test_case['data'],
                                         'edit_resource',
                                         test_case['expected_result'],
                                         xblock_name)
            # Reset resource 0
            url = self.get_handler_url('edit_resource', xblock_name)
            self.client.post(url, json.dumps(original_data), '')

    def test_flag_resource(self):
        """
        Verify the resource flagging is handled correctly
        """
        self.enroll_staff(self.staff_user.email)
        # Add resources, assume correct here, tested in test_add_resource
        for resource, xblock_name in itertools.product(self.test_recommendations,
                                                       self.xblock_names):
            self.add_resource(resource, xblock_name)

        test_cases = [
            [
                {
                    'expected_result': {'Success': True},
                    'data': {
                        'id': 0,
                        'isProblematic': True,
                        'reason': ''
                    }
                    # Flag resource 0 as problematic, without providing the reason
                },
                {
                    'expected_result': {'Success': True},
                    'data': {
                        'id': 1,
                        'isProblematic': True,
                        'reason': 'reason 1'
                    }
                    # Flag resource 1 as problematic, and provide a reason
                },
                {
                    'expected_result': {'Success': True, 'oldReason': ''},
                    'data': {
                        'id': 0,
                        'isProblematic': True,
                        'reason': 'reason 0'
                    }
                    # Update the reason for resource 0
                },
                {
                    'expected_result': {'Success': True, 'oldReason': 'reason 0'},
                    'data': {
                        'id': 0,
                        'isProblematic': False,
                        'reason': ''
                    }
                }
                # Flag resource 0 as non-problematic
            ],
            [
                {
                    'expected_result': {'Success': True},
                    'data': {
                        'id': 1,
                        'isProblematic': True,
                        'reason': 'Reason'
                    }
                }
                # Student 1 can't see the flag of student 0, thus, there is no oldReason for resource 1
            ]
        ]

        for test_case_list in test_cases:
            for test_case in test_case_list:
                for key, val in test_case['data'].iteritems():
                    test_case['expected_result'][key] = val

        for test_cases_list, student in zip(test_cases, self.STUDENT_INFO):
            # Change user
            self.logout()
            self.enroll_student(student[0], student[1])
            for test_case, xblock_name in itertools.product(test_cases_list,
                                                            self.xblock_names):
                self.check_ajax_event_result(test_case['data'],
                                             'flag_resource',
                                             test_case['expected_result'],
                                             xblock_name)

    def test_student_is_user_staff(self):
        """
        Verify student is not a staff
        """
        # Check only one block since this handler only retrieves user-scope variable
        self.enroll_student(self.STUDENT_INFO[0][0], self.STUDENT_INFO[0][1])
        url = self.get_handler_url('is_user_staff')
        result = json.loads(self.client.post(url, {}, '').content)
        self.assertFalse(result['is_user_staff'])

    def test_staff_is_user_staff(self):
        """
        Verify staff is a staff
        """
        # Check only one block since this handler only retrieves user-scope variable
        self.enroll_staff(self.staff_user.email)
        url = self.get_handler_url('is_user_staff')
        result = json.loads(self.client.post(url, {}, '').content)
        self.assertTrue(result['is_user_staff'])

    def test_set_s3_info(self):
        """
        Verify the s3 information setting
        """
        # Check only one block since we can't tell whether the two blocks affect each
        # other from the return in this handler (will be checked in test_upload_screenshot)
        self.enroll_student(self.STUDENT_INFO[0][0], self.STUDENT_INFO[0][1])
        test_cases = [
            {
                'expected_result': {
                    'Success': False,
                    'error': 'Set S3 information without permission'
                },
                'data': {
                    'aws_access_key': 'access key',
                    'aws_secret_key': 'secret key',
                    'bucketName': 'bucket name',
                    'uploadedFileDir': '/'
                }
            },  # Students have no right to set s3 information
            {
                'expected_result': {'Success': True},
                'data': {
                    'aws_access_key': 'access key',
                    'aws_secret_key': 'secret key',
                    'bucketName': 'bucket name',
                    'uploadedFileDir': '/'
                }
            }  # Staff has the right to set s3 information
        ]
        for key, value in test_cases[1]['data'].iteritems():
            test_cases[1]['expected_result'][key] = value

        for index in range(0, len(test_cases)):
            if index == 1:
                self.logout()
                self.enroll_staff(self.staff_user.email)
            self.check_ajax_event_result(test_cases[index]['data'],
                                         'set_s3_info',
                                         test_cases[index]['expected_result'])

    def test_upload_screenshot(self):
        """
        Verify the file type checking in the file uploading method is successful
        We don't check whether the file is uploaded successfully to S3 or not
        """
        self.enroll_staff(self.staff_user.email)
        # Check whether the s3 information setting is independent in the two blocks
        for xblock_name in self.xblock_names:
            # Upload file when the information of s3 is not set
            temp = tempfile.NamedTemporaryFile(prefix='upload_', suffix='.csv')
            data = {}
            data['file'] = temp
            response = self.client.post(self.get_handler_url('upload_screenshot',
                                                             xblock_name), data)
            self.assertEqual(response.content, 'IMPROPER_S3_SETUP')
            self.check_for_get_xblock_page_code(200)

            # Set fake s3 information
            # Assume correct, test in test_set_s3_info
            data = {}
            data['aws_access_key'] = 'access key'
            data['aws_secret_key'] = 'secret key'
            data['bucketName'] = 'bucket name'
            data['uploadedFileDir'] = '/'
            self.client.post(self.get_handler_url('set_s3_info', xblock_name),
                             json.dumps(data), '')

            test_cases = [
                {
                    'suffixes': '.gif',
                    'magic_number': '89504e470d0a1a0a',
                    'response': 'FILE_TYPE_ERROR'
                },
                {
                    'suffixes': '.jpg',
                    'magic_number': '89504e470d0a1a0a',
                    'response': 'FILE_TYPE_ERROR'
                },
                {
                    'suffixes': '.png',
                    'magic_number': '474946383761',
                    'response': 'FILE_TYPE_ERROR'
                },
                {
                    'suffixes': '.jpg',
                    'magic_number': '474946383761',
                    'response': 'FILE_TYPE_ERROR'
                },
                {
                    'suffixes': '.png',
                    'magic_number': 'ffd8ffd9',
                    'response': 'FILE_TYPE_ERROR'
                },
                {
                    'suffixes': '.gif',
                    'magic_number': 'ffd8ffd9',
                    'response': 'FILE_TYPE_ERROR'
                }
            ]
            # Upload file with correct extension name but wrong magic number
            for test_case in test_cases:
                temp = tempfile.NamedTemporaryFile(prefix='upload_',
                                                   suffix=test_case['suffixes'],
                                                   delete=False)
                temp.seek(0)
                temp.write(test_case['magic_number'].decode('hex'))
                temp.flush()
                url = self.get_handler_url('upload_screenshot', xblock_name)
                response = self.client.post(url, {'file': open(temp.name, 'r')})
                self.assertEqual(response.content, test_case['response'])
                self.check_for_get_xblock_page_code(200)

        test_cases = [
            {
                'suffixes': '.csv',
                'magic_number': 'ffd8ffd9',
                'response': 'FILE_TYPE_ERROR'
                # Upload file with wrong extension name
            },
            {
                'suffixes': '.png',
                'magic_number': '89504e470d0a1a0a',
                'response': 'IMPROPER_S3_SETUP'
                # Upload file with correct extension name and magic number
                # It fails because we set fake s3 information here
            },
            {
                'suffixes': '.gif',
                'magic_number': '474946383961',
                'response': 'IMPROPER_S3_SETUP'
                # Upload file with correct extension name and magic number
                # It fails because we set fake s3 information here
            },
            {
                'suffixes': '.gif',
                'magic_number': '474946383761',
                'response': 'IMPROPER_S3_SETUP'
                # Upload file with correct extension name and magic number
                # It fails because we set fake s3 information here
            },
            {
                'suffixes': '.jpg',
                'magic_number': 'ffd8ffd9',
                'response': 'IMPROPER_S3_SETUP'
                # Upload file with correct extension name and magic number
                # It fails because we set fake s3 information here
            }
        ]

        for test_case in test_cases:
            temp = tempfile.NamedTemporaryFile(prefix='upload_',
                                               suffix=test_case['suffixes'],
                                               delete=False)
            temp.seek(0)
            temp.write(test_case['magic_number'].decode('hex'))
            temp.flush()
            data = {}
            data['file'] = open(temp.name, 'r')
            url = self.get_handler_url('upload_screenshot')
            response = self.client.post(url, data)
            self.assertEqual(response.content, test_case['response'])
            self.check_for_get_xblock_page_code(200)
