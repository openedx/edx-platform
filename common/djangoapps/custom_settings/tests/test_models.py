import pytest

from .factories import CustomSettingsFactory


@pytest.mark.django_db
def test_save_custom_settings_and_no_prior_course_short_id():
    """Assert that course short id is set to 100, when CustomSettings is saved"""
    custom_settings = CustomSettingsFactory(course_short_id=None)
    assert custom_settings.course_short_id == 100


@pytest.mark.django_db
def test_save_custom_settings_increment_course_short_id():
    """Assert that course short id is incremented properly when CustomSettings is saved"""
    CustomSettingsFactory(course_short_id=200)
    CustomSettingsFactory(course_short_id=300)
    custom_settings = CustomSettingsFactory(course_short_id=None)
    assert custom_settings.course_short_id == 301


@pytest.mark.django_db
@pytest.mark.parametrize(
    'seo_tags, expected',
    [
        pytest.param(
            '{"title":"test", "description":"test", "keywords":"test", "robots":"test", "utm_tag1":"value1"}',
            {'title': 'test', 'description': 'test', 'keywords': 'test', 'robots': 'test',
             'utm_params': {'utm_tag1': 'value1'}},
            id='all_seo_tags'
        ),
        pytest.param(
            '{"title":"test", "description":"test", "dummy":"dummy"}',
            {'title': 'test', 'description': 'test', 'keywords': '', 'robots': '', 'utm_params': {}},
            id='some_seo_tags_and_dummy_tags'
        )
    ]
)
def test_get_course_meta_tags(seo_tags, expected):
    """All test cases for course meta tag function"""
    custom_settings = CustomSettingsFactory(seo_tags=seo_tags)
    course_meta_tags = custom_settings.get_course_meta_tags()
    assert course_meta_tags == expected
