""" Test Constants. """

PHILU_BOT_NAME = 'philubot'


TEST_RUBRIC_DICT = {
        'prompts': [
            {
              'description': u'Test prompt.'
            }
        ],
        'criteria': [
            {
                'prompt': 'Test Prompt.',
                'feedback': 'optional',
                'label': 'Ideas',
                'order_num': 0,
                'options': [
                    {
                        'order_num': 0,
                        'explanation': 'Test explanation',
                        'points': 1,
                        'name': 'Poor',
                        'label': 'Poor'
                    },
                    {
                        'order_num': 1,
                        'explanation': 'Test explanation',
                        'points': 3,
                        'name': 'Fair',
                        'label': 'Fair'
                    },
                    {
                        'order_num': 2,
                        'explanation': 'Test explanation',
                        'points': 5,
                        'name': 'Good',
                        'label': 'Good'
                    }
                ],
                'name': 'Ideas'
            },
            {
                'order_num': 1,
                'prompt': 'Test prompt',
                'options': [
                    {
                        'order_num': 0,
                        'explanation': 'Test explanation',
                        'points': 0,
                        'name': 'Poor',
                        'label': 'Poor'
                    },
                    {
                        'order_num': 1,
                        'explanation': 'Test explanation',
                        'points': 1,
                        'name': 'Fair',
                        'label': 'Fair'
                    },
                    {
                        'order_num': 2,
                        'explanation': 'Test explanation',
                        'points': 3,
                        'name': 'Good',
                        'label': 'Good'
                    },
                    {
                        'order_num': 3,
                        'explanation': 'Test explanation',
                        'points': 3,
                        'name': 'Excellent',
                        'label': 'Excellent'
                    }
                ],
                'name': 'Content',
                'label': 'Content'
            }
        ]
    }

TWO_POINT_RUBRIC_DICTIONARY = {
    "prompts": [],
    "criteria": [
      {
        "prompt": "Test Prompt.",
        "feedback": "optional",
        "label": "Ideas",
        "order_num": 0,
        "options": [
          {
            "order_num": 0,
            "explanation": "Test Explanation.",
            "points": 0,
            "name": "Poor",
            "label": "Poor"
          },
          {
            "order_num": 1,
            "explanation": "Test Explanation.",
            "points": 3,
            "name": "Fair",
            "label": "Fair"
          }
        ],
        "name": "Ideas"
      },
      {
        "order_num": 1,
        "label": "Content",
        "prompt": "Assess the content of the submission",
        "options": [
          {
            "order_num": 0,
            "explanation": "Test Explanation.",
            "points": 0,
            "name": "Poor",
            "label": "Poor"
          },
          {
            "order_num": 1,
            "explanation": "Test Explanation.",
            "points": 1,
            "name": "Fair",
            "label": "Fair"
          }
        ],
        "name": "Content"
      }
    ]
}

THREE_POINT_RUBRIC_DICTIONARY = {
    "prompts": [],
    "criteria": [
      {
        "prompt": "Determine if there is a unifying theme or main idea.",
        "feedback": "optional",
        "label": "Ideas",
        "order_num": 0,
        "options": [
          {
            "order_num": 0,
            "explanation": "Test Explanation.",
            "points": 0,
            "name": "Poor",
            "label": "Poor"
          },
          {
            "order_num": 1,
            "explanation": "Test Explanation.",
            "points": 3,
            "name": "Fair",
            "label": "Fair"
          },
          {
            "order_num": 2,
            "explanation": "Test Explanation.",
            "points": 3,
            "name": "Good",
            "label": "Good"
          }
        ],
        "name": "Ideas"
      },
      {
        "order_num": 1,
        "label": "Content",
        "prompt": "Assess the content of the submission",
        "options": [
          {
            "order_num": 0,
            "explanation": "Test Explanation.",
            "points": 0,
            "name": "Poor",
            "label": "Poor"
          },
          {
            "order_num": 1,
            "explanation": "Test Explanation.",
            "points": 1,
            "name": "Fair",
            "label": "Fair"
          },
          {
            "order_num": 2,
            "explanation": "Test Explanation.",
            "points": 3,
            "name": "Good",
            "label": "Good"
          }
        ],
        "name": "Content"
      }
    ]
}

COURSE_CHILD_STRUCTURE = {
    "course": "chapter",
    "chapter": "sequential",
    "sequential": "vertical",
    "vertical": "html",
}
