"""
Constants for the learner pathway application tests
"""

import json


class LearnerPathwayProgressOutputs:
    """
    Model tests constants for the learner pathway progress model.

    .. no_pii:
    """
    snapshot_from_discovery = json.dumps({
        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b1",
        "status": "active",
        "steps": [
            {
                "uuid": "9d91b42a-f3e4-461a-b9e1-e53a4fc927ed",
                "min_requirement": 2,
                "courses": [
                    {
                        "key": "AA+AA101",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2020"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2021"
                            }
                        ]
                    },
                    {
                        "key": "AA+AA102",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2022"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2023"
                            }
                        ]
                    }
                ],
                "programs": [
                    {
                        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b2"
                    }
                ]
            },
            {
                "uuid": "9d91b42a-f3e4-461a-b9e1-e53a4fc927ef",
                "min_requirement": 2,
                "courses": [
                    {
                        "key": "AA+AA103",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2024"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2025"
                            }
                        ]
                    },
                    {
                        "key": "AA+AA104",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2026"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2027"
                            }
                        ]
                    }
                ],
                "programs": [
                    {
                        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b3"
                    }
                ]
            }
        ]
    })
    updated_learner_progress1 = json.dumps({
        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b1",
        "status": "active",
        "steps": [
            {
                "uuid": "9d91b42a-f3e4-461a-b9e1-e53a4fc927ed",
                "min_requirement": 2,
                "courses": [
                    {
                        "key": "AA+AA101",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2020"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2021"
                            }
                        ],
                        "status": "IN_PROGRESS"
                    },
                    {
                        "key": "AA+AA102",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2022"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2023"
                            }
                        ],
                        "status": "IN_PROGRESS"
                    }
                ],
                "programs": [
                    {
                        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b2",
                        "status": "NOT_STARTED"
                    }
                ],
                "status": 0.0
            },
            {
                "uuid": "9d91b42a-f3e4-461a-b9e1-e53a4fc927ef",
                "min_requirement": 2,
                "courses": [
                    {
                        "key": "AA+AA103",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2024"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2025"
                            }
                        ],
                        "status": "IN_PROGRESS"
                    },
                    {
                        "key": "AA+AA104",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2026"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2027"
                            }
                        ],
                        "status": "IN_PROGRESS"
                    }
                ],
                "programs": [
                    {
                        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b3",
                        "status": "NOT_STARTED"
                    }
                ],
                "status": 0.0
            }
        ]
    })
    updated_learner_progress2 = json.dumps({
        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b1",
        "status": "active",
        "steps": [
            {
                "uuid": "9d91b42a-f3e4-461a-b9e1-e53a4fc927ed",
                "min_requirement": 2,
                "courses": [
                    {
                        "key": "AA+AA101",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2020"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2021"
                            }
                        ],
                        "status": "IN_PROGRESS"
                    },
                    {
                        "key": "AA+AA102",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2022"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2023"
                            }
                        ],
                        "status": "NOT_STARTED"
                    }
                ],
                "programs": [
                    {
                        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b2",
                        "status": "NOT_STARTED"
                    }
                ],
                "status": 0.0
            },
            {
                "uuid": "9d91b42a-f3e4-461a-b9e1-e53a4fc927ef",
                "min_requirement": 2,
                "courses": [
                    {
                        "key": "AA+AA103",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2024"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2025"
                            }
                        ],
                        "status": "IN_PROGRESS"
                    },
                    {
                        "key": "AA+AA104",
                        "course_runs": [
                            {
                                "key": "course-v1:test-enterprise+test1+2026"
                            },
                            {
                                "key": "course-v1:test-enterprise+test1+2027"
                            }
                        ],
                        "status": "NOT_STARTED"
                    }
                ],
                "programs": [
                    {
                        "uuid": "1f301a72-f344-4a31-9e9a-e0b04d8d86b3",
                        "status": "NOT_STARTED"
                    }
                ],
                "status": 0.0
            }
        ]
    })
