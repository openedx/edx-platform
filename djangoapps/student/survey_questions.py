import random
import settings

def exit_survey_list_for_student(student):
    # Right now, we just randomly pick some questions from random_questions
    common_questions = exit_survey_questions['common_questions']
    randomized_questions = exit_survey_questions['random_questions']
            
    #If we use random.sample on randomized_questions directly, it will re-arrange the questions
    if not settings.DEBUG_SURVEY:
        chosen_indices = random.sample( range( len(randomized_questions) ), 6 )
    else:
        #In debug mode, we show all surveys
        chosen_indices = range( len(randomized_questions) )
                
    chosen_questions = [ randomized_questions[i] for i in sorted(chosen_indices)]
    
    survey_list = common_questions + chosen_questions
    return survey_list
    
    

exit_survey_questions = {
    'common_questions' : [
        {'type' : 'checkbox',
        'question_name' : 'future_classes',
        'label' : 'Please inform me of future classes offered by edX.'},
        
        {'type' : 'checkbox',
        'question_name' : 'future_offerings',
        'label' : 'Please inform me of opportunities to help with future offerings of 6.002x, such as staffing discussiong forums or developing content.'},
        
        #I think we should combine this question with the one above it. Mostly to shorten the survey
        {'type' : 'checkbox',
        'question_name' : '6002x_updates',
        'label' : 'Please subscribe me to periodic updates about additional topics, refreshers, and follow-ups for topics in 6.002x.'},
    ],
    'random_questions' : [
        {'type' : 'radio',
        'question_name' : 'teach_ee',
        'label' : 'Do you teach electrical engineering (EE)?',
        'choices' : [
            'I teach EE in college/university.',
            'I teach EE in high school/secondary school.',
            'I do not teach EE.',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'highest_degree',
        'label' : 'What is the highest degree you have completed?',
        'choices' : [
            'I have a PhD in a science or engineering field.',
            'I have a PhD in another field.',
            'I have a master\'s or professional degree.',
            'I have a bachelor\'s degree.',
            'I completed secondary/high school.',
            'I completed junior secondary/high school.',
            'I completed elementary school.',
        ]},
        
        {'type' : 'short_field',
        'question_name' : 'age',
        'label' : 'What is your age?',
        },
        
        # We could also do this as a radio Male/Female/Other
        {'type' : 'short_field',
        'question_name' : 'gender',
        'label' : 'What is your gender?',
        },
        
        {'type' : 'radio',
        'question_name' : 'scholarship_secondary',
        'label' : 'Did you receive any scholarship or financial assistance to attend <strong>secondary school</strong>?',
        'choices' : [
            'Yes',
            'No',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'scholarship_college',
        'label' : 'Did you receive any scholarship or financial assistanche to attend <strong>college/university</strong>?',
        'choices' : [
            'Yes',
            'No',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'ee_level',
        'label' : 'What is the highest level electrical engineering (EE) course you have taken? ',
        'choices' : [
            'More than one year of EE in college/university',
            'One year or less of EE in college/university',
            'More than one year of EE in high school/secondary school',
            'One year or less of EE in high school/secondary school',
            'Self-taught in EE',
            'None of the above',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'math_level',
        'label' : 'What is the highest level mathematics course you have taken?',
        'choices' : [
            'Mathematics beyond calculus of a single variable in college/university',
            'Single variable calculus',
            'Algebra',
            'Self-taught in mathematics',
            'None of the above',
        ]},
        
        {'type' : 'select_many',
        'question_name' : 'why_course',
        'label' : 'Why are you taking this course? (Check all that apply.)',
        'choices' : [
            'Interest in topic only',
            'Preparation for advanced placement exam',
            'Preparation for advanced standing exam',
            'Review of EE concepts',
            'Employment/job advancement opportunities',
            'Other',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'weekly_hours',
        'label' : 'How many hours per week on average did you work on this course?',
        'choices' : [
            '0-2',
            '3-5',
            '6-9',
            '10 or more',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'internet_access',
        'label' : 'Where do you access the MITx website most frequently?',
        'choices' : [
            'At home',
            'At the home of a friend or family member outside your home',
            'At school',
            'Internet cafe or other public space',
            'Other',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'work_offline',
        'label' : 'Have you worked <b>offline</b> with anyone on the MITx material?',
        'choices' : [
            'I worked with another person who is also completing the course.',
            'I worked with someone who teaches or has expertise in this area.',
            'I worked completely on my own.',
            'Other',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'online_course_count',
        'label' : 'How many online courses have you taken?',
        'choices' : [
            '1',
            '2',
            '3',
            '4',
            '5 or more',
        ]},
        
        {'type' : 'short_field',
        'question_name' : 'home_language',
        'label' : 'Language most spoken in your home:',
        },
        
        {'type' : 'short_field',
        'question_name' : 'home_postal_code',
        'label' : 'Postal code (home address):',
        },
        
        # This question seems redundant with the above question. Remove it? Does the whole world have postal codes?
        # Also, we already asked for a location
        {'type' : 'short_field',
        'question_name' : 'home_country',
        'label' : 'Country (home address):',
        },
        
        {'type' : 'short_field',
        'question_name' : 'race',
        'label' : 'With what race/ethnic group do you most strongly identify?',
        },
        
        {'type' : 'radio',
        'question_name' : 'book_count',
        'label' : 'How many books are there in your home? <br/><em>(There are usually about 40 books per meter of shelving. Do not include magazines, newspapers, or schoolbooks in your estimate.)</em>',
        'choices' : [
            '0-10 books',
            '11-25 books',
            '26-100 books',
            '101-200 books',
            '201-500 books',
            'More than 500 books',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'computer_in_home',
        'label' : 'Did you have a computer in your home?',
        'choices' : [
            'Yes',
            'No',
        ]},
        
        {'type' : 'radio',
        'question_name' : 'parents_engineering',
        'label' : 'Do either of your parents have any training or experience in engineering?',
        'choices' : [
            'Yes',
            'No',
            'I don\'t know',
        ]},
        
        #We used to have two of these questions, one for their mom and one for their dad. That might not make sense for some students.
        {'type' : 'radio',
        'question_name' : 'engineering',
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
