exit_survey_questions = {
    'common_questions' : [
        {'type' : 'survey_checkbox',
        'question_name' : 'survey_future_classes',
        'label' : 'Please inform me of future classes offered by edX.'},
        
        {'type' : 'survey_checkbox',
        'question_name' : 'survey_future_offerings',
        'label' : 'Please inform me of opportunities to help with future offerings of 6.002x, such as staffing discussiong forums or developing content.'},
        
        {'type' : 'survey_checkbox',
        'question_name' : 'survey_6002x_updates',
        'label' : 'Please subscribe me to periodic updates about additional topics, refreshers, and follow-ups for topics in 6.002x.'},
    ],
    'random_questions' : [
        {'type' : 'survey_radio',
        'question_name' : 'survey_teach_ee',
        'label' : 'Do you teach electrical engineering (EE)?',
        'choices' : [
            'I teach EE in college/university.',
            'I teach EE in high school/secondary school.',
            'I do not teach EE.',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_highest_degree',
        'label' : 'What is the highest degree you have completed?',
        'choices' : [
            'I have a PhD in a science or engineering field.',
            'I have a PhD in another field.',
            'I have a masters or professional degree.',
            'I have a bachelors degree.',
            'I completed secondary/high school.',
            'I completed junior secondary/high school.',
            'I completed elementary school.',
        ]},
        
        {'type' : 'survey_short_field',
        'question_name' : 'survey_age',
        'label' : 'What is your age?',
        },
        
        {'type' : 'survey_short_field',
        'question_name' : 'survey_gender',
        'label' : 'What is your gender?',
        },
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_scholarship_secondary',
        'label' : 'Did you receive any scholarship or financial assistance to attend secondary school?',
        'choices' : [
            'Yes',
            'No',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_scholarship_college',
        'label' : 'Did you receive any scholarship or financial assistanche to attend college/university?',
        'choices' : [
            'Yes',
            'No',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_ee_level',
        'label' : 'What is the highest level electrical engineering (EE) course you have taken? ',
        'choices' : [
            ' more than one year of EE in college/university',
            ' one year or less of EE in college/university',
            ' more than one year of EE in high school/secondary school',
            ' one year or less of EE in high school/secondary school',
            ' self-taught in EE',
            ' none of the above',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_math_level',
        'label' : 'What is the highest level mathematics course you have taken?',
        'choices' : [
            ' mathematics beyond calculus of a single variable in college/university',
            ' single variable calculus',
            ' algebra',
            ' self-taught in mathematics',
            ' none of the above',
        ]},
        
        {'type' : 'survey_check',
        'question_name' : 'survey_why_course',
        'label' : 'Why are you taking this course? (Check all that apply.)',
        'choices' : [
            'Interest in topic only',
            'Preparation for advanced placement exam',
            'Preparation for advanced standing exam',
            'Review of EE concepts',
            'Employment/job advancement opportunities',
            'Other',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_weekly_hours',
        'label' : 'How many hours a week on average did you work on this course? ',
        'choices' : [
            '0-2',
            '3-5',
            '6-9',
            '10 or more',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_internet_access',
        'label' : 'Where do you access the MITx website most frequently?',
        'choices' : [
            'At home',
            'At the home of a friend or family member outside your home',
            'At school',
            'Internet cafe or other public space',
            'Other',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_work_offline',
        'label' : 'Have you worked offline with anyone on the MITx material?',
        'choices' : [
            'I worked with another person who is also completing the course.',
            'I worked with someone who teaches or has expertise in this area.',
            'I worked completely on my own.',
            'Other',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_online_course_count',
        'label' : 'How many online courses have you taken?',
        'choices' : [
            '1',
            '2',
            '3',
            '4',
            '5 or more',
        ]},
        
        {'type' : 'survey_short_field',
        'question_name' : 'survey_home_language',
        'label' : 'Language most spoken in your home:',
        },
        
        {'type' : 'survey_short_field',
        'question_name' : 'survey_home_postal_code',
        'label' : 'Postal code (home address):',
        },
        
        {'type' : 'survey_short_field',
        'question_name' : 'survey_home_country',
        'label' : 'Country (home address):',
        },
        
        {'type' : 'survey_short_field',
        'question_name' : 'survey_race',
        'label' : 'With what race/ethnic group do you most strongly identify?',
        },
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_online_course_count',
        'label' : 'How many books are there in your home? (There are usually about 40 books per meter of shelving. Do not include magazines, newspapers, or schoolbooks in your estimate.)',
        'choices' : [
            '0-10 books',
            '11-25 books',
            '26-100 books',
            '101-200 books',
            '201-500 books',
            'More than 500 books',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_computer_in_home',
        'label' : 'Did you have a computer in your home?',
        'choices' : [
            'Yes',
            'No',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey_parents_engineering',
        'label' : 'Do either of your parents have any training or experience in engineering?',
        'choices' : [
            'Yes',
            'No',
            'I don\'t know',
        ]},
        
        {'type' : 'survey_radio',
        'question_name' : 'survey__engineering',
        'label' : 'What is the highest level of schooling completed by one of your parents? (Please choose the answer you think fits best.)',
        'choices' : [
            'PhD degree',
            'Post-graduate, professional degree, or master\'s degree',
            'Bachelor\'s degree',
            'Vocational/technical training',
            'High school or secondary school',
            'Primary school',
            'Did not complete primary school',
        ]},
    ]
}