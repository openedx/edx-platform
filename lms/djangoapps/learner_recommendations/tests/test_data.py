""" Mocked data for testing """

mock_course_data = [
    {
        "key": "edx+HL0",
        "uuid": "0f8cb2c9-589b-4d1e-88c1-b01a02db3a9c",
        "title": "Title 0",
        "image": {
            "src": "https://www.logo_image_url0.com"
        },
        "prospectusPath": "course/https://www.marketing_url0.com",
        "owners": [
            {
                "key": "org-0",
                "name": "org 0",
                "logoImageUrl": "https://discovery.com/organization/logos/org-0.png"
            }
        ],
        "activeCourseRun": {
            "key": "course-v1:Test+2023_T0",
            "marketingUrl": "https://www.marketing_url0.com"
        },
        "courseType": "executive-education"
    },
    {
        "key": "edx+HL1",
        "uuid": "1f8cb2c9-589b-4d1e-88c1-b01a02db3a9c",
        "title": "Title 1",
        "image": {
            "src": "https://www.logo_image_url1.com"
        },
        "prospectusPath": "course/https://www.marketing_url1.com",
        "owners": [
            {
                "key": "org-1",
                "name": "org 1",
                "logoImageUrl": "https://discovery.com/organization/logos/org-1.png"
            }
        ],
        "activeCourseRun": {
            "key": "course-v1:Test+2023_T1",
            "marketingUrl": "https://www.marketing_url1.com"
        },
        "courseType": "executive-education"
    }
]

mock_cross_product_data = [
    {
        "title": "Title 0",
        "image": {
            "src": "https://www.logo_image_url0.com"
        },
        "prospectusPath": "course/https://www.marketing_url0.com",
        "owners": [
            {
                "key": "org-0",
                "name": "org 0",
                "logoImageUrl": "https://discovery.com/organization/logos/org-0.png"
            }
        ],
        "courseType": "executive-education"
    },
    {
        "title": "Title 1",
        "image": {
            "src": "https://www.logo_image_url1.com"
        },
        "prospectusPath": "course/https://www.marketing_url1.com",
        "owners": [
            {
                "key": "org-1",
                "name": "org 1",
                "logoImageUrl": "https://discovery.com/organization/logos/org-1.png"
            }
        ],
        "courseType": "executive-education"
    },
]

mock_amplitude_data = [
    *mock_cross_product_data,
    {
        "title": "Title 2",
        "image": {
            "src": "https://www.logo_image_url2.com"
        },
        "prospectusPath": "course/https://www.marketing_url2.com",
        "owners": [
            {
                "key": "org-2",
                "name": "org 2",
                "logoImageUrl": "https://discovery.com/organization/logos/org-2.png"
            }
        ],
        "courseType": "executive-education"
    },
    {
        "title": "Title 3",
        "image": {
            "src": "https://www.logo_image_url3.com"
        },
        "prospectusPath": "course/https://www.marketing_url3.com",
        "owners": [
            {
                "key": "org-3",
                "name": "org 3",
                "logoImageUrl": "https://discovery.com/organization/logos/org-3.png"
            }
        ],
        "courseType": "executive-education"
    }
]


def get_general_recommendations():
    """Returns 5 general recommendations with the necessary fields"""

    courses = []

    base_course = {
        "course_key": "MITx+1.00",
        "title": "Introduction to Computer Science and Programming Using Python",
        "url_slug": "introduction-to-computer-science-and-programming-7",
        "course_type": "credit-verified-audit",
        "logo_image_url": "https://discovery.com/organization/logos/org-1.png",
        "marketing_url": "https://www.marketing_url.com",
        "owners": [
            {
                "key": "MITx",
                "name": "Massachusetts Institute of Technology",
                "logo_image_url": "https://discovery.com/organization/logos/org-1.png",
            }
        ],
        "image": {
            "src": "https://link.to.an.image.png"
        },
    }

    for _ in range(5):
        courses.append(base_course)

    return courses


mock_amplitude_and_cross_product_course_data = {
    "crossProductCourses": mock_cross_product_data,
    "amplitudeCourses": mock_amplitude_data
}

mock_cross_product_course_data = {
    "courses": mock_course_data
}

mock_amplitude_course_data = {
    "amplitudeCourses": mock_amplitude_data
}

mock_cross_product_recommendation_keys = {
    "edx+HL0": ["edx+HL1", "edx+HL2"],
    "edx+BZ0": ["edx+BZ1", "edx+BZ2"],
}
