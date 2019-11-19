import copy


def create_torphycase_data(torphycase_dict, badge_type, all_badges, earned_user_badges, enrolled_courses_data):
    """
    This method creates data for tophycase badges. It has a hierarchy of enrolled courses, badge type, earned and
    yet to be earned badges with complete detail
    :param torphycase_dict: The dictionary object to hold tophycase data
    :param badge_type: Type of badge to be added under course
    :param all_badges: All badges of type badge_type
    :param earned_user_badges: Badges earned by user
    :param enrolled_courses_data: Courses enrolled by user
    :return: None
    """
    for course_id, display_name in enrolled_courses_data:

        # make deepcopy of badges so that earned badge flag can be added for specific course
        all_badges_copy = copy.deepcopy(all_badges)

        # append data if key exists otherwise
        # set default value first before appending data
        torphycase_dict.setdefault(display_name, []).append({
            badge_type: all_badges_copy
        })

        # add earned badge date in dict
        for badge in all_badges_copy:
            for earned_badge in earned_user_badges:
                if badge['id'] == earned_badge['badge_id'] and course_id == earned_badge['course_id']:
                    # earned date indicate badge is earned
                    badge['date_earned'] = earned_badge['date_earned']
