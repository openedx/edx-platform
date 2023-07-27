from enum import Enum

TOTAL_PROBLEM_SCORE = 5
MAX_SKILLS_SCORE = 15
INTRO_RATING_ASSESSMENT_RESPONSE = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
OUTRO_RATING_ASSESSMENT_RESPONSE = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

class ProblemSetting:
    IS_SKILL_ASSESSMENT = 'is_skill_assessment'
    IS_JOURNAL_ENTRY = 'is_journal_entry'
    IS_EXPORTABLE = 'is_exportable'
    IS_STUDENT_ANSWER = 'is_student_answer'


class ProblemTypes:
    JOURNAL = 'journal_responses'
    SINGLE_CHOICE  = 'single_choice'
    MULTIPLE_CHOICE = 'multiple_choice'
    SHORT_ANSWER = 'short_answers'
    LIKERT = 'likert'

    __ALL__ = (JOURNAL, SINGLE_CHOICE, MULTIPLE_CHOICE, SHORT_ANSWER,)
    STRING_TYPE_PROBLEMS = (JOURNAL, SHORT_ANSWER,)
    CHOICE_TYPE_PROBLEMS = (SINGLE_CHOICE, MULTIPLE_CHOICE,)

    SKILL_ASSESSMENT_PROBLEMS = (LIKERT,)
    STUDENT_ANSWER_PROBLEMS = (SINGLE_CHOICE, MULTIPLE_CHOICE, SHORT_ANSWER,)
    JOURNAL_PROBLEMS = (SINGLE_CHOICE, MULTIPLE_CHOICE, SHORT_ANSWER,)
    PDF_PROBLEMS = (SHORT_ANSWER,)


class SkillAssessmentTypes:

    """
    Skill Assessment choices for the classes
    """
    LIKERT = 'likert'

    __ALL__ = (LIKERT,)
    __MODEL_CHOICES__ = (
        (skill_assessment_type, skill_assessment_type) for skill_assessment_type in __ALL__
    )

class SkillAssessmentResponseTime:

    """
    Skill Assessment choices for the classes
    """
    START_OF_YEAR = 'start_of_year'
    END_OF_YEAR = 'end_of_year'

    __ALL__ = (START_OF_YEAR, END_OF_YEAR)
    __MODEL_CHOICES__ = (
        (response_time, response_time) for response_time in __ALL__
    )

JOURNAL_STYLE = '''{{"blocks":[{{"key":"540nn","text":"{0}","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{{}}}}],"entityMap":{{}}}}'''


class SkillReflectionQuestionType(Enum):
    LIKERT = 2
    NUANCE_INTERROGATION = 1

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)
    @classmethod
    def to_list(cls):
        return [
            {"name": i.name, "value": i.value} for i in cls
        ]
