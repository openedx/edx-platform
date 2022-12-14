TOTAL_PROBLEM_SCORE = 5
MAX_SKILLS_SCORE = 15
INTRO_RATING_ASSESSMENT_RESPONSE = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
OUTRO_RATING_ASSESSMENT_RESPONSE = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

class ProblemTypes:
    JOURNAL = 'journal_responses'
    SINGLE_CHOICE  = 'single_choice'
    MULTIPLE_CHOICE = 'multiple_choice'
    SHORT_ANSWER = 'short_answers'

    __ALL__ = (JOURNAL, SINGLE_CHOICE, MULTIPLE_CHOICE, SHORT_ANSWER,)
    STRING_TYPE_PROBLEMS = (JOURNAL, SHORT_ANSWER,)
    CHOICE_TYPE_PROBLEMS = (SINGLE_CHOICE, MULTIPLE_CHOICE,)
    SHOW_IN_STUDENT_ANSWERS_PROBLEMS = (SINGLE_CHOICE, MULTIPLE_CHOICE, SHORT_ANSWER,)


JOURNAL_STYLE = '''{{"blocks":[{{"key":"540nn","text":"{0}","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{{}}}}],"entityMap":{{}}}}'''
