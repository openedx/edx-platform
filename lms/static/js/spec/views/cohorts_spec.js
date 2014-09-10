define(['backbone', 'jquery', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/views/cohorts', 'js/collections/cohort', 'string_utils'],
    function (Backbone, $, AjaxHelpers, TemplateHelpers, CohortsView, CohortCollection) {
        describe("Cohorts View", function () {
            var catLoversInitialCount = 123, dogLoversInitialCount = 456, unknownUserMessage,
                createMockCohorts, createCohortsView, cohortsView, requests, verifyMessage, verifyHeader;

            createMockCohorts = function (catCount, dogCount) {
                return {
                    cohorts: [
                        {
                            id: 1,
                            name: 'Cat Lovers',
                            user_count: catCount || catLoversInitialCount
                        },
                        {
                            id: 2,
                            name: 'Dog Lovers',
                            user_count: dogCount || dogLoversInitialCount
                        }
                    ]
                };
            };

            createCohortsView = function (test, initialCohortID) {
                var cohorts = new CohortCollection(createMockCohorts(), {parse: true});
                cohorts.url = '/mock_service';
                requests = AjaxHelpers.requests(test);
                cohortsView = new CohortsView({
                    model: cohorts
                });
                cohortsView.render();
                if (initialCohortID) {
                    cohortsView.$('.cohort-select').val(initialCohortID).change();
                }
            };

            verifyMessage = function(expectedTitle, messageType, expectedDetails, expectedAction) {
                var numDetails = cohortsView.$('.summary-items').children().length;

                expect(cohortsView.$('.message-title').text().trim()).toBe(expectedTitle);
                expect(cohortsView.$('div.message').hasClass('message-' + messageType)).toBe(true);
                if (expectedAction) {
                    expect(cohortsView.$('.message-actions .action-primary').text()).toBe(expectedAction);
                }
                else {
                    expect(cohortsView.$('.message-actions .action-primary').length).toBe(0);
                }
                if (expectedDetails) {
                    expect(numDetails).toBe(expectedDetails.length);
                    cohortsView.$('.summary-item').each(function (index) {
                       expect($(this).text().trim()).toBe(expectedDetails[index]);
                    });
                }
                else {
                    expect(numDetails).toBe(0);
                }
            };

            verifyHeader = function(expectedCohortId, expectedTitle, expectedCount) {
                var header = cohortsView.$('.cohort-management-group-header');
                expect(cohortsView.$('.cohort-select').val()).toBe(expectedCohortId.toString());
                expect(cohortsView.$('.cohort-select option:selected').text()).toBe(
                    interpolate_text(
                        '{title} ({count})', {title: expectedTitle, count: expectedCount}
                    )
                );
                expect(header.find('.title-value').text()).toBe(expectedTitle);
                expect(header.find('.group-count').text()).toBe(
                    interpolate_ntext(
                        '(contains {count} student)',
                        '(contains {count} students)',
                        expectedCount,
                        {count: expectedCount}
                    )
                );
            };

            unknownUserMessage = function (name) {
                return "Unknown user: " +  name;
            };

            beforeEach(function () {
                setFixtures("<div></div>");
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohorts');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-selector');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-editor');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/notification');
            });

            describe("Cohort Selector", function () {
                it('has no initial selection', function () {
                    createCohortsView(this);
                    expect(cohortsView.$('.cohort-select').val()).toBe('');
                    expect(cohortsView.$('.cohort-management-group-header .title-value').text()).toBe('');
                });

                it('can select a cohort', function () {
                    createCohortsView(this, "1");
                    verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                });

                it('can switch cohort', function () {
                    createCohortsView(this, "1");
                    cohortsView.$('.cohort-select').val("2").change();
                    verifyHeader(2, 'Dog Lovers', dogLoversInitialCount);
                });
            });

            describe("Add Students Button", function () {
                var getStudentInput, addStudents, respondToAdd, respondToRefresh;

                getStudentInput = function() {
                    return cohortsView.$('.cohort-management-group-add-students');
                };

                addStudents = function(students) {
                    getStudentInput().val(students);
                    cohortsView.$('.cohort-management-group-add-form').submit();
                };

                respondToAdd = function(result) {
                    AjaxHelpers.respondWithJson(
                        requests,
                        _.extend({ unknown: [], added: [], present: [], changed: [], success: true }, result)
                    );
                };

                respondToRefresh = function(catCount, dogCount) {
                    AjaxHelpers.respondWithJson(requests, createMockCohorts(catCount, dogCount));
                };

                it('shows an error when adding with no students specified', function() {
                    createCohortsView(this, "1");
                    addStudents('    ');
                    expect(requests.length).toBe(0);
                    verifyMessage('Please enter a username or email.', 'error');
                    expect(getStudentInput().val()).toBe('');
                });

                it('can add a single student', function() {
                    var catLoversUpdatedCount = catLoversInitialCount + 1;
                    createCohortsView(this, "1");
                    addStudents('student@sample.com');
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/1/add', 'users=student%40sample.com');
                    respondToAdd({ added: ['student@sample.com'] });
                    respondToRefresh(catLoversUpdatedCount, dogLoversInitialCount);
                    verifyHeader(1, 'Cat Lovers', catLoversUpdatedCount);
                    verifyMessage('1 student has been added to this cohort group', 'confirmation');
                    expect(getStudentInput().val()).toBe('');
                });

                it('shows an error when adding a student that does not exist', function() {
                    createCohortsView(this, "1");
                    addStudents('unknown@sample.com');
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/1/add', 'users=unknown%40sample.com');
                    respondToAdd({ unknown: ['unknown@sample.com'] });
                    respondToRefresh(catLoversInitialCount, dogLoversInitialCount);
                    verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                    verifyMessage('There was an error when trying to add students:', 'error',
                        [unknownUserMessage('unknown@sample.com')]
                    );
                    expect(getStudentInput().val()).toBe('unknown@sample.com');
                });

                it('shows a "view all" button when more than 5 students do not exist', function() {
                    var sixUsers = 'unknown1@sample.com, unknown2@sample.com, unknown3@sample.com, unknown4@sample.com, unknown5@sample.com, unknown6@sample.com';
                    createCohortsView(this, "1");

                    addStudents(sixUsers);
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/1/add',
                        'users=' + sixUsers.replace(/@/g, "%40").replace(/, /g, "%2C+")
                    );
                    respondToAdd({ unknown: [
                        'unknown1@sample.com',
                        'unknown2@sample.com',
                        'unknown3@sample.com',
                        'unknown4@sample.com',
                        'unknown5@sample.com',
                        'unknown6@sample.com']
                    });
                    respondToRefresh(catLoversInitialCount + 6, dogLoversInitialCount);
                    verifyMessage('There were 6 errors when trying to add students:', 'error',
                        [
                            unknownUserMessage('unknown1@sample.com'), unknownUserMessage('unknown2@sample.com'),
                            unknownUserMessage('unknown3@sample.com'), unknownUserMessage('unknown4@sample.com'),
                            unknownUserMessage('unknown5@sample.com')
                        ],
                        'View all errors'
                    );
                    expect(getStudentInput().val()).toBe(sixUsers);
                    // Click "View all"
                    cohortsView.$('a.action-primary').click();
                    verifyMessage('There were 6 errors when trying to add students:', 'error',
                        [
                            unknownUserMessage('unknown1@sample.com'), unknownUserMessage('unknown2@sample.com'),
                            unknownUserMessage('unknown3@sample.com'), unknownUserMessage('unknown4@sample.com'),
                            unknownUserMessage('unknown5@sample.com'), unknownUserMessage('unknown6@sample.com')
                        ]
                    );
                });

                it('shows students moved from one cohort to another', function() {
                    var sixUsers = 'moved1@sample.com, moved2@sample.com, moved3@sample.com, alreadypresent@sample.com';
                    createCohortsView(this, "1");

                    addStudents(sixUsers);
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/1/add',
                        'users=' + sixUsers.replace(/@/g, "%40").replace(/, /g, "%2C+")
                    );
                    respondToAdd({
                        changed: [
                            {email: 'moved1@sample.com', name: 'moved1', previous_cohort: 'group 2', username: 'moved1'},
                            {email: 'moved2@sample.com', name: 'moved2', previous_cohort: 'group 2', username: 'moved2'},
                            {email: 'moved3@sample.com', name: 'moved3', previous_cohort: 'group 3', username: 'moved3'}
                        ],
                        present: ['alreadypresent@sample.com']
                    });
                    respondToRefresh();

                    verifyMessage('3 students have been added to this cohort group', 'confirmation',
                        [
                            "2 students were removed from group 2",
                            "1 student was removed from group 3",
                            "1 student was already in the cohort group"
                        ]
                    );
                    expect(getStudentInput().val()).toBe('');
                });

                it('shows a message when the add fails', function() {
                    createCohortsView(this, "1");
                    addStudents('student@sample.com');
                    AjaxHelpers.respondWithError(requests);
                    verifyMessage('Error adding students.', 'error');
                    expect(getStudentInput().val()).toBe('student@sample.com');
                });

                it('clears an error message on subsequent add', function() {
                    createCohortsView(this, "1");

                    // First verify that an error is shown
                    addStudents('student@sample.com');
                    AjaxHelpers.respondWithError(requests);
                    verifyMessage('Error adding students.', 'error');

                    // Now verify that the error is removed on a subsequent add
                    addStudents('student@sample.com');
                    respondToAdd({ added: ['student@sample.com'] });
                    respondToRefresh(catLoversInitialCount + 1, dogLoversInitialCount);
                    verifyMessage('1 student has been added to this cohort group', 'confirmation');
                });
            });
        });
    });
