
import uuid


def get_mocked_journal_access():
    return [
        {
            "expiration_date": "2050-11-08",
            "uuid": uuid.uuid4(),
            "journal": {
                "name": "dummy-name1",
                "organization": "edx",
                "journalaboutpage": {
                    "slug": "dummy-slug1",
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
                    "slug": "dummy-slug2",
                    "card_image_absolute_url": "dummy-url"
                }
            }
        }
    ]


def get_mocked_journal_bundle():
    return {
        "uuid": "1918b738-979f-42cb-bde0-13335366fa86",
        "title": "dummy-title",
        "partner": "edx",
        "journals": [
            {
                "title": "dummy-title",
                "sku": "ASZ1GZ",
                "card_image_url": "dummy-url",
                "slug": "dummy-title",
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
    }


def get_mocked_journals():
    return [
        {
            "title": "dummy-title1",
            "card_image_url": "dummy-url1",
            "slug": "dummy-title1",
            "access_length": "8 weeks",
            "organization": "edx"
        },
        {
            "title": "dummy-title2",
            "card_image_url": "dummy-url2",
            "slug": "dummy-title2",
            "access_length": "8 weeks",
            "organization": "edx"
        }
    ]


def get_mocked_pricing_data():
    return {
        "currency": "USD",
        "discount_value": 0.3,
        "is_discounted": False,
        "total_incl_tax": 23.01,
        "purchase_url": "dummy-url",
        "total_incl_tax_excl_discounts": 40
    }
