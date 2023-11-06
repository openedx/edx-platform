
from .models import ToggleFeatureCourse , ToggleFeatureUser


def extract_features(feature_obj):
    features = []
    if feature_obj:
        if feature_obj[0].is_discussion:
            features.append('discussion')
        if feature_obj[0].is_chatGPT:
            features.append('chatGPT')
        if feature_obj[0].is_feedback:
            features.append('feedback')
        if feature_obj[0].is_search:
            features.append('search')
        if feature_obj[0].is_date_and_progress:
            features.append('dates')
    else:
        features = ['discussion', 'chatGPT', 'feedback', 'search', 'dates']

    return features




def featureCourse(course_id):
    feature_course = ToggleFeatureCourse.findCourseToggeFeature(course_id=course_id)

    return extract_features(feature_course)


def featureUser(user_id):
    feature_user = ToggleFeatureUser.findUserToggleFeature(user_id=user_id)
    return extract_features(feature_user)



def toggleFeature (course_id , user_id):
    feature_user = featureUser(user_id)
    feature_course = featureCourse(course_id)
    list_feature = ['discussion', 'chatGPT', 'feedback', 'search', 'dates']
    # Create sets from list_feature, feature_user, and feature_course for easy set operations
    set_feature = set(list_feature)
    set_user = set(feature_user)
    set_course = set(feature_course)

    # Remove features that are not in both feature_user and feature_course
    set_feature = set_feature.intersection(set_user, set_course)

    # Convert the result back to a list
    filter_feature = list(set_feature)
    return filter_feature