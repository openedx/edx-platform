""" Returns the dummy data for journals endpoint of discovery."""
import uuid
from functools import wraps
from openedx.features.journals.api import WAFFLE_SWITCHES


def override_switch(switch, active):
    """
    Overrides the given waffle switch to `active` boolean.

    Arguments:
        switch(str): switch name
        active(bool): A boolean representing (to be overridden) value
    """
    def decorate(function):
        """
        decorator function
        """
        @wraps(function)
        def inner(*args, **kwargs):
            with WAFFLE_SWITCHES.override(switch, active=active):
                function(*args, **kwargs)
        return inner

    return decorate


def get_mocked_journal_access():
    """
    Returns the dummy data of journal access
    """
    return [
        {
            "expiration_date": "2050-11-08",
            "uuid": uuid.uuid4(),
            "journal": {
                "name": "dummy-name1",
                "organization": "edx",
                "journalaboutpage": {
                    "id": "5",
                    "card_image_absolute_url": "dummy-url"
                }
            }
        },
        {
            "expiration_date": "2050-10-08",
            "uuid": uuid.uuid4(),
            "journal": {
                "name": "dummy-name2",
                "organization": "edx",
                "journalaboutpage": {
                    "id": "5",
                    "card_image_absolute_url": "dummy-url"
                }
            }
        }
    ]


def get_mocked_journal_bundles():
    """
    Returns the dummy data of journal bundle.
    """
    return [{
        "uuid": "1918b738-979f-42cb-bde0-13335366fa86",
        "title": "dummy-title",
        "partner": "edx",
        "organization": "edx",
        "journals": [
            {
                "title": "dummy-title",
                "sku": "ASZ1GZ",
                "card_image_url": "dummy-url",
                "about_page_id": "5",
                "access_length": "8 weeks",
                "short_description": "dummy short description"
            }
        ],
        "courses": [
            {
                "short_description": "dummy short description",
                "course_runs": [
                    {
                        "key": "course-v1:ABC+ABC101+2015_T1",
                        "title": "Matt edX test course",
                        "start": "2015-01-08T00:00:00Z",
                        "end": "2016-12-30T00:00:00Z",
                        "image": {
                            "src": "dummy/url"
                        },
                        "seats": [
                            {
                                "type": "verified",
                                "sku": "unit03",
                                "bulk_sku": "2DF467D"
                            }
                        ]
                    }
                ]
            }
        ],
        "applicable_seat_types": ["credit", "honor", "verified"]
    }]


def get_mocked_journals():
    """
    Returns the dummy data of journals
    """
    return [
        {
            "title": "dummy-title1",
            "card_image_url": "dummy-url1",
            "about_page_id": "5",
            "access_length": 60,
            "organization": "edx"
        },
        {
            "title": "dummy-title2",
            "card_image_url": "dummy-url2",
            "about_page_id": "5",
            "access_length": 60,
            "organization": "edx"
        }
    ]


def get_mocked_pricing_data():
    """
    Returns the dummy data for e-commerce pricing
    """
    return {
        "currency": "USD",
        "discount_value": 0.3,
        "is_discounted": False,
        "total_incl_tax": 23.01,
        "purchase_url": "dummy-url",
        "total_incl_tax_excl_discounts": 40
    }
