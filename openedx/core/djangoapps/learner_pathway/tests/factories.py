"""
Factories for LearnerPathwayProgress models.
"""

import json
from uuid import uuid4

import factory
from factory.django import DjangoModelFactory

from common.djangoapps.student.tests.factories import UserFactory

from ..models import LearnerPathwayProgress


class LearnerPathwayProgressFactory(DjangoModelFactory):
    """ Simple factory class for generating LearnerPathwayProgress """

    class Meta:
        model = LearnerPathwayProgress

    user = factory.SubFactory(UserFactory)
    learner_pathway_uuid = factory.LazyFunction(uuid4)

    @factory.lazy_attribute
    def learner_pathway_progress(self):
        return json.dumps({
            'uuid': str(self.learner_pathway_uuid),
            'status': 'active',
            'steps': [
                {
                    'uuid': '9d91b42a-f3e4-461a-b9e1-e53a4fc927ed',
                    'min_requirement': 2,
                    'courses': [
                        {
                            'key': 'AA+AA101',
                            'course_runs': [
                                {
                                    'key': 'course-v1:test-enterprise+test1+2020'
                                },
                                {
                                    'key': 'course-v1:test-enterprise+test1+2021'
                                }
                            ],
                        },
                        {
                            'key': 'AA+AA102',
                            'course_runs': [
                                {
                                    'key': 'course-v1:test-enterprise+test1+2022'
                                },
                                {
                                    'key': 'course-v1:test-enterprise+test1+2023'
                                }
                            ],
                        }
                    ],
                    'programs': [
                        {
                            'uuid': '1f301a72-f344-4a31-9e9a-e0b04d8d86b2'
                        }
                    ]
                },
                {
                    'uuid': '9d91b42a-f3e4-461a-b9e1-e53a4fc927ef',
                    'min_requirement': 2,
                    'courses': [
                        {
                            'key': 'AA+AA103',
                            'course_runs': [
                                {
                                    'key': 'course-v1:test-enterprise+test1+2024',
                                },
                                {
                                    'key': 'course-v1:test-enterprise+test1+2025'
                                }
                            ],
                        },
                        {
                            'key': 'AA+AA104',
                            'course_runs': [
                                {
                                    'key': 'course-v1:test-enterprise+test1+2026'
                                },
                                {
                                    'key': 'course-v1:test-enterprise+test1+2027'
                                }
                            ],
                        }
                    ],
                    'programs': [
                        {
                            'uuid': '1f301a72-f344-4a31-9e9a-e0b04d8d86b3'
                        }
                    ]
                }
            ]
        })
