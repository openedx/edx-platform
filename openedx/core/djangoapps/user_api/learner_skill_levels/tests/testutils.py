"""
Utilities for unit tests of learner skill levels.
"""

DUMMY_CATEGORIES_RESPONSE = {
    "job": "Digital Product Manager",
    "skill_categories": [
        {
            "name": "Information Technology",
            "id": 1,
            "skills": [
                {"id": 3, "name": "Technology Roadmap"},
                {"id": 12, "name": "Python"},
                {"id": 2, "name": "MongoDB"}
            ],
            "skills_subcategories": [
                {
                    "id": 1,
                    "name": "Databases",
                    "skills": [
                        {"id": 1, "name": "Query Languages"},
                        {"id": 2, "name": "MongoDB"},
                    ]
                },
                {
                    "id": 2,
                    "name": "IT Management",
                    "skills": [
                        {"id": 3, "name": "Technology Roadmap"},
                    ]
                },
            ]
        },
        {
            "name": "Finance",
            "id": 2,
            "skills": [
                {"id": 4, "name": "Accounting"},
                {"id": 5, "name": "TQM"},
            ],
            "skills_subcategories": [
                {
                    "id": 3,
                    "name": "Auditing",
                    "skills": [
                        {"id": 4, "name": "Accounting"},
                        {"id": 5, "name": "TQM"},
                    ]
                },
                {
                    "id": 4,
                    "name": "Management",
                    "skills": [
                        {"id": 6, "name": "Financial Management"},
                    ]
                },
            ]
        },
    ]
}

DUMMY_CATEGORIES_WITH_SCORES = {
    "job": "Digital Product Manager",
    "skill_categories": [
        {
            "name": "Information Technology",
            "id": 1,
            "skills": [
                {"id": 3, "name": "Technology Roadmap", "score": 1},
                {"id": 12, "name": "Python", "score": 2},
                {"id": 2, "name": "MongoDB", "score": 3}
            ],
            "user_score": 0.8,
        },
        {
            "name": "Finance",
            "id": 2,
            "skills": [
                {"id": 1, "name": "Query Languages", "score": 1},
                {"id": 4, "name": "System Design", "score": 2},
            ],
            "user_score": 0.3,
        },
    ]
}

DUMMY_USER_SCORES_MAP = {
    "Information Technology": [0.1, 0.3, 0.5, 0.7],
    "Finance": [0.2, 0.4, 0.6, 0.8]

}

DUMMY_USERNAMES_RESPONSE = {
    "usernames": [
        'test_user_1',
        'test_user_2',
        'test_user_3',
        'test_user_4',
        'test_user_5',
        'test_user_6',
    ]
}

DUMMY_COURSE_DATA_RESPONSE = {
    "key": "AWS+OTP",
    "uuid": "fe1a9ad4-a452-45cd-80e5-9babd3d43f96",
    "title": "Demonstration Course",
    "level_type": 'Advanced',
    "skill_names": ["python", "MongoDB", "Data Science"]
}
