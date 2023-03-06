"""
APIs for learner skill levels.
"""
from .utils import get_skills_score, calculate_user_skill_score, generate_skill_score_mapping


def get_learner_skill_levels(user, top_categories):
    """
    Evaluates learner's skill levels in the given job category. Only considers skills for the categories
    and not their sub-categories.

    Params:
        user: user for each score is being calculated.
        top_categories (List, string): A list of fields (as strings) of job categories and their skills.
    Returns:
        top_categories: Categories with scores appended to skills.
    """

    # get a skill to score mapping for every course user has passed
    skill_score_mapping = generate_skill_score_mapping(user)
    for skill_category in top_categories:
        category_skills = skill_category['skills']
        get_skills_score(category_skills, skill_score_mapping)
        skill_category['user_score'] = calculate_user_skill_score(category_skills)
        skill_category['edx_average_score'] = None
        sub_categories = skill_category['skills_subcategories']
        for sub_category in sub_categories:
            subcategory_skills = sub_category['skills']
            get_skills_score(subcategory_skills, skill_score_mapping)

    return top_categories
