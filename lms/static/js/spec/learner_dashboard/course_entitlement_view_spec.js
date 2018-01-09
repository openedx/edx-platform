define([
    'backbone',
    'underscore',
    'jquery',
    'js/learner_dashboard/models/course_entitlement_model',
    'js/learner_dashboard/views/course_entitlement_view'
], function(Backbone, _, $, CourseEntitlementModel, CourseEntitlementView) {
    'use strict';

    describe('Course Entitlement View', function() {
        var view = null,
            setupView,
            selectOptions,
            entitlementAvailableSessions,
            initialSessionId,
            alreadyEnrolled,
            hasSessions,
            entitlementUUID = 'a9aiuw76a4ijs43u18',
            testSessionIds = ['test_session_id_1', 'test_session_id_2'];

        setupView = function(isAlreadyEnrolled, hasAvailableSessions) {
            setFixtures('<div class="course-entitlement-selection-container"></div>');
            alreadyEnrolled = (typeof isAlreadyEnrolled !== 'undefined') ? isAlreadyEnrolled : true;
            hasSessions = (typeof hasAvailableSessions !== 'undefined') ? hasAvailableSessions : true;

            initialSessionId = alreadyEnrolled ? testSessionIds[0] : '';
            entitlementAvailableSessions = [];
            if (hasSessions) {
                entitlementAvailableSessions = [{
                    enrollment_end: null,
                    start: '2019-02-05T05:00:00+00:00',
                    pacing_type: 'instructor_paced',
                    session_id: testSessionIds[0],
                    end: null
                }, {
                    enrollment_end: '2019-12-22T03:30:00Z',
                    start: '2020-01-03T13:00:00+00:00',
                    pacing_type: 'self_paced',
                    session_id: testSessionIds[1],
                    end: '2020-03-09T21:30:00+00:00'
                }];
            }

            view = new CourseEntitlementView({
                el: '.course-entitlement-selection-container',
                triggerOpenBtn: '#course-card-0 .change-session',
                courseCardMessages: '#course-card-0 .messages-list > .message',
                courseTitleLink: '#course-card-0 .course-title a',
                courseImageLink: '#course-card-0 .wrapper-course-image > a',
                dateDisplayField: '#course-card-0 .info-date-block',
                enterCourseBtn: '#course-card-0 .enter-course',
                availableSessions: JSON.stringify(entitlementAvailableSessions),
                entitlementUUID: entitlementUUID,
                currentSessionId: initialSessionId,
                userId: '1',
                enrollUrl: '/api/enrollment/v1/enrollment',
                courseHomeUrl: '/courses/course-v1:edX+DemoX+Demo_Course/course/'
            });
        };

        afterEach(function() {
            if (view) view.remove();
        });

        describe('Initialization of view', function() {
            it('Should create a entitlement view element', function() {
                setupView(false);
                expect(view).toBeDefined();
            });
        });

        describe('Available Sessions Select - Unfulfilled Entitlement', function() {
            beforeEach(function() {
                setupView(false);
                selectOptions = view.$('.session-select').find('option');
            });

            it('Select session dropdown should show all available course runs and a coming soon option.', function() {
                expect(selectOptions.length).toEqual(entitlementAvailableSessions.length + 1);
            });

            it('Self paced courses should have visual indication in the selection option.', function() {
                var selfPacedOptionIndex = _.findIndex(entitlementAvailableSessions, function(session) {
                    return session.pacing_type === 'self_paced';
                });
                var selfPacedOption = selectOptions[selfPacedOptionIndex];
                expect(selfPacedOption && selfPacedOption.text.includes('(Self-paced)')).toBe(true);
            });

            it('Courses with an an enroll by date should indicate so on the selection option.', function() {
                var enrollEndSetOptionIndex = _.findIndex(entitlementAvailableSessions, function(session) {
                    return session.enrollment_end !== null;
                });
                var enrollEndSetOption = selectOptions[enrollEndSetOptionIndex];
                expect(enrollEndSetOption && enrollEndSetOption.text.includes('Open until')).toBe(true);
            });

            it('Title element should correctly indicate the expected behavior.', function() {
                expect(view.$('.action-header').text().includes(
                    'To access the course, select a session.'
                )).toBe(true);
            });
        });

        describe('Available Sessions Select - Unfulfilled Entitlement without available sessions', function() {
            beforeEach(function() {
                setupView(false, false);
            });

            it('Should notify user that more sessions are coming soon if none available.', function() {
                expect(view.$('.action-header').text().includes('More sessions coming soon.')).toBe(true);
            });
        });

        describe('Available Sessions Select - Fulfilled Entitlement', function() {
            beforeEach(function() {
                setupView(true);
                selectOptions = view.$('.session-select').find('option');
            });

            it('Select session dropdown should show available course runs, coming soon and leave options.', function() {
                expect(selectOptions.length).toEqual(entitlementAvailableSessions.length + 2);
            });

            it('Select session dropdown should allow user to leave the current session.', function() {
                var leaveSessionOption = selectOptions[selectOptions.length - 1];
                expect(leaveSessionOption.text.includes('Leave the current session and decide later')).toBe(true);
            });

            it('Currently selected session should be specified in the dropdown options.', function() {
                var selectedSessionIndex = _.findIndex(entitlementAvailableSessions, function(session) {
                    return initialSessionId === session.session_id;
                });
                expect(selectOptions[selectedSessionIndex].text.includes('Currently Selected')).toBe(true);
            });

            it('Title element should correctly indicate the expected behavior.', function() {
                expect(view.$('.action-header').text().includes(
                    'Change to a different session or leave the current session.'
                )).toBe(true);
            });
        });

        describe('Select Session Action Button and popover behavior - Unfulfilled Entitlement', function() {
            beforeEach(function() {
                setupView(false);
            });

            it('Change session button should have the correct text.', function() {
                expect(view.$('.enroll-btn-initial').text() === 'Select Session').toBe(true);
            });

            it('Select session button should show popover when clicked.', function() {
                view.$('.enroll-btn-initial').click();
                expect(view.$('.verification-modal').length > 0).toBe(true);
            });
        });

        describe('Change Session Action Button and popover behavior - Fulfilled Entitlement', function() {
            beforeEach(function() {
                setupView(true);
                selectOptions = view.$('.session-select').find('option');
            });

            it('Change session button should show correct text.', function() {
                expect(view.$('.enroll-btn-initial').text().trim() === 'Change Session').toBe(true);
            });

            it('Switch session button should be disabled when on the currently enrolled session.', function() {
                expect(view.$('.enroll-btn-initial')).toHaveClass('disabled');
            });
        });
    });
}
);
