""" Data shapes used for testing ESG """

# Options split for reuse
example_rubric_options = [
    {
        "order_num": 0,
        "name": "troll",
        "label": "Troll",
        "explanation": "Failing grade",
        "points": 0,
    },
    {
        "order_num": 1,
        "name": "dreadful",
        "label": "Dreadful",
        "explanation": "Failing grade",
        "points": 1,
    },
    {
        "order_num": 2,
        "name": "poor",
        "label": "Poor",
        "explanation": "Failing grade (may repeat)",
        "points": 2,
    },
    {
        "order_num": 3,
        "name": "poor",
        "label": "Poor",
        "explanation": "Failing grade (may repeat)",
        "points": 3,
    },
    {
        "order_num": 4,
        "name": "acceptable",
        "label": "Acceptable",
        "explanation": "Passing grade (may continue to N.E.W.T)",
        "points": 4,
    },
    {
        "order_num": 5,
        "name": "exceeds_expectations",
        "label": "Exceeds Expectations",
        "explanation": "Passing grade (may continue to N.E.W.T)",
        "points": 5,
    },
    {
        "order_num": 6,
        "name": "outstanding",
        "label": "Outstanding",
        "explanation": "Passing grade (will continue to N.E.W.T)",
        "points": 6,
    },
]

example_rubric_options_serialized = [
    {
        "orderNum": 0,
        "name": "troll",
        "label": "Troll",
        "explanation": "Failing grade",
        "points": 0,
    },
    {
        "orderNum": 1,
        "name": "dreadful",
        "label": "Dreadful",
        "explanation": "Failing grade",
        "points": 1,
    },
    {
        "orderNum": 2,
        "name": "poor",
        "label": "Poor",
        "explanation": "Failing grade (may repeat)",
        "points": 2,
    },
    {
        "orderNum": 3,
        "name": "poor",
        "label": "Poor",
        "explanation": "Failing grade (may repeat)",
        "points": 3,
    },
    {
        "orderNum": 4,
        "name": "acceptable",
        "label": "Acceptable",
        "explanation": "Passing grade (may continue to N.E.W.T)",
        "points": 4,
    },
    {
        "orderNum": 5,
        "name": "exceeds_expectations",
        "label": "Exceeds Expectations",
        "explanation": "Passing grade (may continue to N.E.W.T)",
        "points": 5,
    },
    {
        "orderNum": 6,
        "name": "outstanding",
        "label": "Outstanding",
        "explanation": "Passing grade (will continue to N.E.W.T)",
        "points": 6,
    },
]

example_rubric = {
    "rubric_feedback_prompt": "How did this student do?",
    "rubric_feedback_default_text": "For the O.W.L exams, this student...",
    "rubric_criteria": [
        {
            "order_num": 0,
            "name": "potions",
            "label": "Potions",
            "prompt": "How did this student perform in the Potions exam",
            "feedback": "optional",
            "options": example_rubric_options,
        },
        {
            "order_num": 1,
            "name": "charms",
            "label": "Charms",
            "prompt": "How did this student perform in the Charms exam",
            "options": example_rubric_options,
        },
    ],
}

example_submission_list = {
    "b086331a-5c50-428a-8348-5a85e5029299": {
        "submissionUuid": "b086331a-5c50-428a-8348-5a85e5029299",
        "username": "buzz",
        "teamName": None,
        "dateSubmitted": "1969-07-16 13:32:00",
        "dateGraded": None,
        "gradedBy": None,
        "gradingStatus": "ungraded",
        "lockStatus": "unlocked",
        "score": {"pointsEarned": 0, "pointsPossible": 10},
    }
}

example_submission = {
    "text": ["This is the answer"],
    "files": [
        {
            "name": "name_0",
            "description": "description_0",
            "download_url": "www.file_url.com/key_0",
            "size": 123455,
        }
    ],
}

example_assessment = {
    "feedback": "Base Assessment Feedback",
    "score": {
        "pointsEarned": 5,
        "pointsPossible": 6,
    },
    "criteria": [
        {
            "name": "Criterion 1",
            "option": "Three",
            "points": 3,
            "feedback": "Feedback 1",
        },
    ],
}

example_grade_data = {
    "overallFeedback": "was pretty good",
    "criteria": [
        {"name": "Ideas", "feedback": "did alright", "selectedOption": "Fair"},
        {"name": "Content", "selectedOption": "Excellent"},
    ],
}
