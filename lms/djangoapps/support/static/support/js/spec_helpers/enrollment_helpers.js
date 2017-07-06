define([], function () {
    'use strict';

    var testCourse = "course-v1:TestX+T101+2015";
    return {
        TEST_COURSE: testCourse,
        mockEnrollmentData: {
            created: "2015-12-07T18:17:46.210940Z",
            mode: "audit",
            is_active: true,
            user: "test-user",
            course_end: "2017-01-01T00:00:00Z",
            course_start: "2015-01-01T00:00:00Z",
            course_modes: [
                {
                    slug: "audit",
                    name: "Audit",
                    min_price: 0,
                    suggested_prices: "",
                    currency: "usd",
                    expiration_datetime: null,
                    description: null,
                    sku: "6ED7EDC"
                },
                {
                    slug: "verified",
                    name: "Verified Certificate",
                    min_price: 5,
                    suggested_prices: "",
                    currency: "usd",
                    expiration_datetime: null,
                    description: null,
                    sku: "25A5354"
                }
            ],
            enrollment_start: null,
            course_id: testCourse,
            invite_only: false,
            enrollment_end: null,
            verified_price: 5,
            verified_upgrade_deadline: null,
            verification_deadline: null,
            manual_enrollment: {}
        }
    };
});
