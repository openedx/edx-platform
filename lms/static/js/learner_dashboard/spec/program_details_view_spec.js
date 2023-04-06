/* globals setFixtures */

import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import ProgramDetailsView from '../views/program_details_view';

describe('Program Details Header View', () => {
    let view = null;
    const options = {
        programData: {
            subscription_data: {
                is_eligible_for_subscription: false,
                subscription_price: '$39',
                subscription_start_date: '2023-03-18',
                subscription_state: '',
                trial_end_date: '2023-03-18',
                trial_end_time: '3:54 pm',
                trial_length: 7,
            },
            subtitle: '',
            overview: '',
            weeks_to_complete: null,
            corporate_endorsements: [],
            video: null,
            type: 'Test',
            max_hours_effort_per_week: null,
            transcript_languages: [
                'en-us',
            ],
            expected_learning_items: [],
            uuid: '0ffff5d6-0177-4690-9a48-aa2fecf94610',
            title: 'Test Course Title',
            languages: [
                'en-us',
            ],
            subjects: [],
            individual_endorsements: [],
            staff: [
                {
                    family_name: 'Tester',
                    uuid: '11ee1afb-5750-4185-8434-c9ae8297f0f1',
                    bio: 'Dr. Tester, PhD, RD, is an Associate Professor at the School of Nutrition.',
                    profile_image: {},
                    profile_image_url: 'some image',
                    given_name: 'Bob',
                    urls: {
                        blog: null,
                        twitter: null,
                        facebook: null,
                    },
                    position: {
                        organization_name: 'Test University',
                        title: 'Associate Professor of Nutrition',
                    },
                    works: [],
                    slug: 'dr-tester',
                },
            ],
            marketing_slug: 'testing',
            marketing_url: 'someurl',
            status: 'active',
            credit_redemption_overview: '',
            discount_data: {
                currency: 'USD',
                discount_value: 0,
                is_discounted: false,
                total_incl_tax: 300,
                total_incl_tax_excl_discounts: 300,
            },
            full_program_price: 300,
            card_image_url: 'some image',
            faq: [],
            pathway_ids: [2],
            price_ranges: [
                {
                    max: 378,
                    total: 109,
                    min: 10,
                    currency: 'USD',
                },
            ],
            banner_image: {
                large: {
                    url: 'someurl',
                    width: 1440,
                    height: 480,
                },
                small: {
                    url: 'someurl',
                    width: 435,
                    height: 145,
                },
                medium: {
                    url: 'someurl',
                    width: 726,
                    height: 242,
                },
                'x-small': {
                    url: 'someurl',
                    width: 348,
                    height: 116,
                },
            },
            authoring_organizations: [
                {
                    description: '<p>Learning University is home to leading creators, entrepreneurs.</p>',
                    tags: [
                        'contributor',
                    ],
                    name: 'Learning University',
                    homepage_url: null,
                    key: 'LearnX',
                    certificate_logo_image_url: null,
                    marketing_url: 'someurl',
                    logo_image_url: 'https://stage.edx.org/sites/default/files/school/image/logo/learnx.png',
                    uuid: 'de3e9ff0-477d-4496-8cfa-a98f902e5830',
                },
                {
                    description: '<p>The Test University was chartered in 1868.</p>',
                    tags: [
                        'charter',
                        'contributor',
                    ],
                    name: 'Test University',
                    homepage_url: null,
                    key: 'TestX',
                    certificate_logo_image_url: null,
                    marketing_url: 'someurl',
                    logo_image_url: 'https://stage.edx.org/sites/default/files/school/image/logo/ritx.png',
                    uuid: '54bc81cb-b736-4505-aa51-dd2b18c61d84',
                },
            ],
            job_outlook_items: [],
            credit_backing_organizations: [],
            weeks_to_complete_min: 8,
            weeks_to_complete_max: 8,
            min_hours_effort_per_week: null,
            is_learner_eligible_for_one_click_purchase: false,
        },
        courseData: {
            completed: [
                {
                    owners: [
                        {
                            uuid: '766a3716-f962-425b-b56e-e214c019b229',
                            key: 'Testx',
                            name: 'Test University',
                        },
                    ],
                    uuid: '4be8dceb-3454-4fbf-8993-17d563ab41d4',
                    title: 'Who let the dogs out',
                    image: null,
                    key: 'Testx+DOGx002',
                    course_runs: [
                        {
                            upgrade_url: null,
                            image: {
                                src: 'someurl',
                                width: null,
                                description: null,
                                height: null,
                            },
                            max_effort: null,
                            is_enrollment_open: true,
                            course: 'Testx+DOGx002',
                            content_language: null,
                            eligible_for_financial_aid: true,
                            seats: [
                                {
                                    sku: '4250900',
                                    credit_hours: null,
                                    price: '89.00',
                                    currency: 'USD',
                                    upgrade_deadline: null,
                                    credit_provider: '',
                                    type: 'verified',
                                },
                            ],
                            course_url: '/courses/course-v1:Testx+DOGx002+1T2016/',
                            availability: 'Archived',
                            transcript_languages: [],
                            staff: [],
                            announcement: null,
                            end: '2016-10-01T23:59:00Z',
                            uuid: 'f0ac45f5-f0d6-44bc-aeb9-a14e36e963a5',
                            title: 'Who let the dogs out',
                            certificate_url: '/certificates/1730700d89434b718d0d91f8b5d339bf',
                            enrollment_start: null,
                            start: '2017-03-21T22:18:15Z',
                            min_effort: null,
                            short_description: null,
                            hidden: false,
                            level_type: null,
                            type: 'verified',
                            enrollment_open_date: 'Jan 01, 1900',
                            marketing_url: null,
                            is_course_ended: false,
                            instructors: [],
                            full_description: null,
                            key: 'course-v1:Testx+DOGx002+1T2016',
                            enrollment_end: null,
                            reporting_type: 'mooc',
                            advertised_start: null,
                            mobile_available: false,
                            modified: '2017-03-24T14:22:15.609907Z',
                            is_enrolled: true,
                            pacing_type: 'self_paced',
                            video: null,
                            status: 'published',
                        },
                    ],
                },
            ],
            in_progress: [
                {
                    owners: [
                        {
                            uuid: 'c484a523-d396-4aff-90f4-bb7e82e16bf6',
                            key: 'LearnX',
                            name: 'Learning University',
                        },
                    ],
                    uuid: '872ec14c-3b7d-44b8-9cf2-9fa62182e1dd',
                    title: 'Star Trek: The Next Generation',
                    image: null,
                    key: 'LearnX+NGIx',
                    course_runs: [
                        {
                            upgrade_url: 'someurl',
                            image: {
                                src: '',
                                width: null,
                                description: null,
                                height: null,
                            },
                            max_effort: null,
                            is_enrollment_open: true,
                            course: 'LearnX+NGx',
                            content_language: null,
                            eligible_for_financial_aid: true,
                            seats: [
                                {
                                    sku: '44EEB26',
                                    credit_hours: null,
                                    price: '0.00',
                                    currency: 'USD',
                                    upgrade_deadline: null,
                                    credit_provider: null,
                                    type: 'audit',
                                },
                                {
                                    sku: '64AAFBA',
                                    credit_hours: null,
                                    price: '10.00',
                                    currency: 'USD',
                                    upgrade_deadline: '2017-04-29T00:00:00Z',
                                    credit_provider: null,
                                    type: 'verified',
                                },
                            ],
                            course_url: 'someurl',
                            availability: 'Current',
                            transcript_languages: [],
                            staff: [],
                            announcement: null,
                            end: '2017-03-31T12:00:00Z',
                            uuid: 'ce841f5b-f5a9-428f-b187-e6372b532266',
                            title: 'Star Trek: The Next Generation',
                            certificate_url: null,
                            enrollment_start: '2014-03-31T20:00:00Z',
                            start: '2017-03-20T20:50:14Z',
                            min_effort: null,
                            short_description: null,
                            hidden: false,
                            level_type: null,
                            type: 'verified',
                            enrollment_open_date: 'Jan 01, 1900',
                            marketing_url: 'someurl',
                            is_course_ended: false,
                            instructors: [],
                            full_description: null,
                            key: 'course-v1:LearnX+NGIx+3T2016',
                            enrollment_end: null,
                            reporting_type: 'mooc',
                            advertised_start: null,
                            mobile_available: false,
                            modified: '2017-03-24T14:16:47.547643Z',
                            is_enrolled: true,
                            pacing_type: 'instructor_paced',
                            video: null,
                            status: 'published',
                        },
                    ],
                },
            ],
            uuid: '0ffff5d6-0177-4690-9a48-aa2fecf94610',
            not_started: [
                {
                    owners: [
                        {
                            uuid: '766a3716-f962-425b-b56e-e214c019b229',
                            key: 'Testx',
                            name: 'Test University',
                        },
                    ],
                    uuid: '88da08e4-e9ef-406e-95d7-7a178f9f9695',
                    title: 'Introduction to Health and Wellness',
                    image: null,
                    key: 'Testx+EXW100x',
                    course_runs: [
                        {
                            upgrade_url: null,
                            image: {
                                src: 'someurl',
                                width: null,
                                description: null,
                                height: null,
                            },
                            max_effort: null,
                            is_enrollment_open: true,
                            course: 'Testx+EXW100x',
                            content_language: 'en-us',
                            eligible_for_financial_aid: true,
                            seats: [
                                {
                                    sku: '',
                                    credit_hours: null,
                                    price: '0.00',
                                    currency: 'USD',
                                    upgrade_deadline: null,
                                    credit_provider: '',
                                    type: 'audit',
                                },
                                {
                                    sku: '',
                                    credit_hours: null,
                                    price: '10.00',
                                    currency: 'USD',
                                    upgrade_deadline: null,
                                    credit_provider: '',
                                    type: 'verified',
                                },
                            ],
                            course_url: 'someurl',
                            availability: 'Archived',
                            transcript_languages: [
                                'en-us',
                            ],
                            staff: [
                                {
                                    family_name: 'Tester',
                                    uuid: '11ee1afb-5750-4185-8434-c9ae8297f0f1',
                                    bio: 'Dr. Tester, PhD, RD, is a Professor at the School of Nutrition.',
                                    profile_image: {},
                                    profile_image_url: 'someimage.jpg',
                                    given_name: 'Bob',
                                    urls: {
                                        blog: null,
                                        twitter: null,
                                        facebook: null,
                                    },
                                    position: {
                                        organization_name: 'Test University',
                                        title: 'Associate Professor of Nutrition',
                                    },
                                    works: [],
                                    slug: 'dr-tester',
                                },
                            ],
                            announcement: null,
                            end: '2017-03-25T22:18:33Z',
                            uuid: 'a36efd39-6637-11e6-a8e3-22000bdde520',
                            title: 'Introduction to Jedi',
                            certificate_url: null,
                            enrollment_start: null,
                            start: '2016-01-11T05:00:00Z',
                            min_effort: null,
                            short_description: null,
                            hidden: false,
                            level_type: null,
                            type: 'verified',
                            enrollment_open_date: 'Jan 01, 1900',
                            marketing_url: 'someurl',
                            is_course_ended: false,
                            instructors: [],
                            full_description: null,
                            key: 'course-v1:Testx+EXW100x+1T2016',
                            enrollment_end: null,
                            reporting_type: 'mooc',
                            advertised_start: null,
                            mobile_available: true,
                            modified: '2017-03-24T14:18:08.693748Z',
                            is_enrolled: false,
                            pacing_type: 'instructor_paced',
                            video: null,
                            status: 'published',
                        },
                        {
                            upgrade_url: null,
                            image: {
                                src: 'someurl',
                                width: null,
                                description: null,
                                height: null,
                            },
                            max_effort: null,
                            is_enrollment_open: true,
                            course: 'Testx+EXW100x',
                            content_language: null,
                            eligible_for_financial_aid: true,
                            seats: [
                                {
                                    sku: '77AA8F2',
                                    credit_hours: null,
                                    price: '0.00',
                                    currency: 'USD',
                                    upgrade_deadline: null,
                                    credit_provider: null,
                                    type: 'audit',
                                },
                                {
                                    sku: '7EC7BB0',
                                    credit_hours: null,
                                    price: '100.00',
                                    currency: 'USD',
                                    upgrade_deadline: null,
                                    credit_provider: null,
                                    type: 'verified',
                                },
                                {
                                    sku: 'BD436CC',
                                    credit_hours: 10,
                                    price: '378.00',
                                    currency: 'USD',
                                    upgrade_deadline: null,
                                    credit_provider: 'asu',
                                    type: 'credit',
                                },
                            ],
                            course_url: 'someurl',
                            availability: 'Archived',
                            transcript_languages: [],
                            staff: [],
                            announcement: null,
                            end: '2016-07-29T00:00:00Z',
                            uuid: '03b34748-19b1-4732-9ea2-e68da95024e6',
                            title: 'Introduction to Jedi',
                            certificate_url: null,
                            enrollment_start: null,
                            start: '2017-03-22T18:10:39Z',
                            min_effort: null,
                            short_description: null,
                            hidden: false,
                            level_type: null,
                            type: 'credit',
                            enrollment_open_date: 'Jan 01, 1900',
                            marketing_url: null,
                            is_course_ended: false,
                            instructors: [],
                            full_description: null,
                            key: 'course-v1:Testx+EXW100x+2164C',
                            enrollment_end: '2016-06-18T19:00:00Z',
                            reporting_type: 'mooc',
                            advertised_start: null,
                            mobile_available: false,
                            modified: '2017-03-23T16:47:37.108260Z',
                            is_enrolled: false,
                            pacing_type: 'self_paced',
                            video: null,
                            status: 'published',
                        },
                    ],
                },
            ],
        },
        urls: {
            program_listing_url: '/dashboard/programs/',
            commerce_api_url: '/api/commerce/v0/baskets/',
            track_selection_url: '/course_modes/choose/',
            program_record_url: 'http://credentials.example.com/records/programs/UUID',
        },
        userPreferences: {
            'pref-lang': 'en',
        },
        creditPathways: [
            {
                org_name: 'Test Org Name',
                email: 'test@test.com',
                name: 'Name of Test Pathway',
                program_uuids: ['0ffff5d6-0177-4690-9a48-aa2fecf94610'],
                description: 'Test credit pathway description',
                id: 2,
                destination_url: 'edx.org',
            },
        ],
        industryPathways: [
            {
                org_name: 'Test Org Name',
                email: 'test@test.com',
                name: 'Name of Test Pathway',
                program_uuids: ['0ffff5d6-0177-4690-9a48-aa2fecf94610'],
                description: 'Test industry pathway description',
                id: 3,
                destination_url: 'industry.com',
            },
        ],
        programTabViewEnabled: false
    };
    const data = options.programData;

    const testSubscriptionState = (state, heading, body) => {
        const subscriptionData = {
            ...options.programData.subscription_data,
            is_eligible_for_subscription: true,
            subscription_state: state,
        };
        view = initView({
            programData: $.extend({}, options.programData, {
                subscription_data: subscriptionData,
            }),
        });
        view.render();
        expect(view.$('.upgrade-subscription')[0]).toBeInDOM();
        expect(view.$('.upgrade-subscription .upgrade-button'))
            .toContainText(StringUtils.interpolate(heading, subscriptionData));
        expect(view.$('.upgrade-subscription .subscription-info'))
            .toContainText(StringUtils.interpolate(body, subscriptionData));
    };

    const initView = (updates) => {
        const viewOptions = $.extend({}, options, updates);

        return new ProgramDetailsView(viewOptions);
    };

    beforeEach(() => {
        setFixtures('<div class="js-program-details-wrapper"></div>');
    });

    afterEach(() => {
        view.remove();
    });

    it('should exist', () => {
        view = initView();
        view.render();
        expect(view).toBeDefined();
    });

    it('should render the header', () => {
        view = initView();
        view.render();
        expect(view.$('.js-program-header h2').html()).toEqual(data.title);
        expect(view.$('.js-program-header .org-logo')[0].src).toEqual(
            data.authoring_organizations[0].logo_image_url,
        );
        expect(view.$('.js-program-header .org-logo')[1].src).toEqual(
            data.authoring_organizations[1].logo_image_url,
        );
    });

    it('should render the program heading program journey message if program not completed', () => {
        view = initView();
        view.render();
        expect(view.$('.program-heading-title').text()).toEqual('Your Program Journey');
        expect(view.$('.program-heading-message').text().trim()
            .replace(/\s+/g, ' ')).toEqual(
                'Track and plan your progress through the 3 courses in this program. ' +
                'To complete the program, you must earn a verified certificate for each course.',
            );
    });

    it('should render the program heading congratulations message if all courses completed', () => {
        view = initView({
            // Remove remaining courses so all courses are complete
            courseData: $.extend({}, options.courseData, {
                in_progress: [],
                not_started: [],
            }),
        });
        view.render();

        expect(view.$('.program-heading-title').text()).toEqual('Congratulations!');
        expect(view.$('.program-heading-message').text().trim()
            .replace(/\s+/g, ' ')).toEqual(
                'You have successfully completed all the requirements for the Test Course Title Test.',
            );
    });

    it('should render the course list headings', () => {
        view = initView();
        view.render();
        expect(view.$('.course-list-heading .status').text()).toEqual(
            'COURSES IN PROGRESSREMAINING COURSESCOMPLETED COURSES',
        );
        expect(view.$('.course-list-heading .count').text()).toEqual('111');
    });

    it('should render the basic course card information', () => {
        view = initView();
        view.render();
        expect($(view.$('.course-title')[0]).text().trim()).toEqual('Star Trek: The Next Generation');
        expect($(view.$('.enrolled')[0]).text().trim()).toEqual('Enrolled:');
        expect($(view.$('.run-period')[0]).text().trim()).toEqual('Mar 20, 2017 - Mar 31, 2017');
    });

    it('should render certificate information', () => {
        view = initView();
        view.render();
        expect($(view.$('.upgrade-message .card-msg')).text().trim()).toEqual('Certificate Status:');
        expect($(view.$('.upgrade-message .price')).text().trim()).toEqual('$10.00');
        expect($(view.$('.upgrade-button.single-course-run')[0]).text().trim()).toEqual('Upgrade to Verified');
    });

    it('should render full program purchase link', () => {
        view = initView({
            programData: $.extend({}, options.programData, {
                is_learner_eligible_for_one_click_purchase: true,
            }),
        });
        view.render();
        expect($(view.$('.upgrade-button.complete-program')).text().trim()
            .replace(/\s+/g, ' '))
            .toEqual(
                'Upgrade All Remaining Courses ( $300.00 USD )',
            );
    });

    it('should render partial program purchase link', () => {
        view = initView({
            programData: $.extend({}, options.programData, {
                is_learner_eligible_for_one_click_purchase: true,
                discount_data: {
                    currency: 'USD',
                    discount_value: 30,
                    is_discounted: true,
                    total_incl_tax: 300,
                    total_incl_tax_excl_discounts: 270,
                },
            }),
        });
        view.render();
        expect($(view.$('.upgrade-button.complete-program')).text().trim()
            .replace(/\s+/g, ' '))
            .toEqual(
                'Upgrade All Remaining Courses ( $270.00 $300.00 USD )',
            );
    });

    it('should render enrollment information', () => {
        view = initView();
        view.render();
        expect(view.$('.run-select')[0].options.length).toEqual(2);
        expect($(view.$('.select-choice')[0]).attr('for')).toEqual($(view.$('.run-select')[0]).attr('id'));
        expect($(view.$('.enroll-button button')[0]).text().trim()).toEqual('Enroll Now');
    });

    it('should send analytic event when purchase button clicked', () => {
        const properties = {
            category: 'partial bundle',
            label: 'Test Course Title',
            uuid: '0ffff5d6-0177-4690-9a48-aa2fecf94610',
        };
        view = initView({
            programData: $.extend({}, options.programData, {
                is_learner_eligible_for_one_click_purchase: true,
                variant: 'partial',
            }),
        });
        view.render();
        $('.complete-program').click();
        // Verify that analytics event fires when the purchase button is clicked.
        expect(window.analytics.track).toHaveBeenCalledWith(
            'edx.bi.user.dashboard.program.purchase',
            properties,
        );
    });

    it('should render the get subscription link if program is subscription eligible', () => {
        testSubscriptionState(
            'pre',
            'Start {trial_length}-Day free trial',
            '{subscription_price}/month subscription after trial ends. Cancel anytime.'
        );
    });

    it('should render appropriate subscription text when subscription is active with trial', () => {
        testSubscriptionState(
            'active_trial',
            'Manage my subscription',
            'Active trial ends {trial_end_date} at {trial_end_time}'
        );
    });

    it('should render appropriate subscription text when subscription is active', () => {
        testSubscriptionState(
            'active',
            'Manage my subscription',
            'Your next billing date is {subscription_billing_date}'
        );
    });

    it('should render appropriate subscription text when subscription is inactive', () => {
        testSubscriptionState(
            'inactive',
            'Restart my subscription',
            'Unlock verified access to all courses for {subscription_price}/month. Cancel anytime.'
        );
    });
});
