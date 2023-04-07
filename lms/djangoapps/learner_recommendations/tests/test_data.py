""" Mocked data for testing """

mock_course_data = {
    "courses": [
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
}

mock_cross_product_recommendation_keys = {
    "edx+HL0": ["edx+HL1", "edx+HL2"],
    "edx+BZ0": ["edx+BZ1", "edx+BZ2"],
}
