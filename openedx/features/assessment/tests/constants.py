"""
Constants for assessment unit tests
"""
PHILU_BOT_NAME = 'philubot'

TWO_POINT_RUBRIC_DICTIONARY = {
    'prompts': [],
    'criteria': [
        {
            'prompt': 'Test Prompt.',
            'feedback': 'optional',
            'label': 'Ideas',
            'order_num': 0,
            'options': [
                {
                    'order_num': 0,
                    'explanation': 'Test Explanation.',
                    'points': 0,
                    'name': 'Poor',
                    'label': 'Poor'
                },
                {
                    'order_num': 1,
                    'explanation': 'Test Explanation.',
                    'points': 3,
                    'name': 'Fair',
                    'label': 'Fair'
                }
            ],
            'name': 'Ideas'
        },
        {
            'order_num': 1,
            'label': 'Content',
            'prompt': 'Assess the content of the submission',
            'options': [
                {
                    'order_num': 0,
                    'explanation': 'Test Explanation.',
                    'points': 0,
                    'name': 'Poor',
                    'label': 'Poor'
                },
                {
                    'order_num': 1,
                    'explanation': 'Test Explanation.',
                    'points': 1,
                    'name': 'Fair',
                    'label': 'Fair'
                }
            ],
            'name': 'Content'
        }
    ]
}

THREE_POINT_RUBRIC_DICTIONARY = {
    'prompts': [],
    'criteria': [
        {
            'prompt': 'Determine if there is a unifying theme or main idea.',
            'feedback': 'optional',
            'label': 'Ideas',
            'order_num': 0,
            'options': [
                {
                    'order_num': 0,
                    'explanation': 'Test Explanation.',
                    'points': 0,
                    'name': 'Poor',
                    'label': 'Poor'
                },
                {
                    'order_num': 1,
                    'explanation': 'Test Explanation.',
                    'points': 3,
                    'name': 'Fair',
                    'label': 'Fair'
                },
                {
                    'order_num': 2,
                    'explanation': 'Test Explanation.',
                    'points': 3,
                    'name': 'Good',
                    'label': 'Good'
                }
            ],
            'name': 'Ideas'
        },
        {
            'order_num': 1,
            'label': 'Content',
            'prompt': 'Assess the content of the submission',
            'options': [
                {
                    'order_num': 0,
                    'explanation': 'Test Explanation.',
                    'points': 0,
                    'name': 'Poor',
                    'label': 'Poor'
                },
                {
                    'order_num': 1,
                    'explanation': 'Test Explanation.',
                    'points': 1,
                    'name': 'Fair',
                    'label': 'Fair'
                },
                {
                    'order_num': 2,
                    'explanation': 'Test Explanation.',
                    'points': 3,
                    'name': 'Good',
                    'label': 'Good'
                }
            ],
            'name': 'Content'
        }
    ]
}
