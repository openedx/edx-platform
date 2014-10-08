define(['backbone', 'jquery', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/views/cohorts', 'js/collections/cohort', 'string_utils'],
    function (Backbone, $, AjaxHelpers, TemplateHelpers, CohortsView, CohortCollection) {
        describe("Cohorts View", function () {
            var catLoversInitialCount = 123, dogLoversInitialCount = 456, unknownUserMessage,
                createMockCohort, createMockCohorts, createCohortsView, cohortsView, requests, respondToRefresh,
                verifyMessage, verifyNoMessage, verifyDetailedMessage, verifyHeader;

            createMockCohort = function (name, id, user_count) {
                return {
                    id: id || 1,
                    name: name,
                    user_count: user_count || 0
                };
            };

            createMockCohorts = function (catCount, dogCount) {
                return {
                    cohorts: [
                        createMockCohort('Cat Lovers', 1, catCount || catLoversInitialCount),
                        createMockCohort('Dog Lovers', 2, dogCount || dogLoversInitialCount)
                    ]
                };
            };

            createCohortsView = function (test, initialCohortID, initialCohorts) {
                var cohorts = new CohortCollection(initialCohorts || createMockCohorts(), {parse: true});
                cohorts.url = '/mock_service';
                requests = AjaxHelpers.requests(test);
                cohortsView = new CohortsView({
                    model: cohorts
                });
                cohortsView.render();
                if (initialCohortID) {
                    cohortsView.$('.cohort-select').val(initialCohortID.toString()).change();
                }
            };

            respondToRefresh = function(catCount, dogCount) {
                AjaxHelpers.respondWithJson(requests, createMockCohorts(catCount, dogCount));
            };

            verifyMessage = function(expectedTitle, expectedMessageType, expectedAction, hasDetails) {
                expect(cohortsView.$('.message-title').text().trim()).toBe(expectedTitle);
                expect(cohortsView.$('div.message')).toHaveClass('message-' + expectedMessageType);
                if (expectedAction) {
                    expect(cohortsView.$('.message-actions .action-primary').text().trim()).toBe(expectedAction);
                }
                else {
                    expect(cohortsView.$('.message-actions .action-primary').length).toBe(0);
                }
                if (!hasDetails) {
                    expect(cohortsView.$('.summary-items').length).toBe(0);
                }
            };

            verifyNoMessage = function() {
                expect(cohortsView.$('.message').length).toBe(0);
            };

            verifyDetailedMessage = function(expectedTitle, expectedMessageType, expectedDetails, expectedAction) {
                var numDetails = cohortsView.$('.summary-items').children().length;
                verifyMessage(expectedTitle, expectedMessageType, expectedAction, true);
                expect(numDetails).toBe(expectedDetails.length);
                cohortsView.$('.summary-item').each(function (index) {
                    expect($(this).text().trim()).toBe(expectedDetails[index]);
                });
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
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/add-cohort-form');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-selector');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-editor');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/notification');
            });

            it("Show an error if no cohorts are defined", function() {
                createCohortsView(this, null, { cohorts: [] });
                verifyMessage(
                    'You currently have no cohort groups configured',
                    'warning',
                    'Add Cohort Group'
                );
            });

            describe("Cohort Selector", function () {
                it('has no initial selection', function () {
                    createCohortsView(this);
                    expect(cohortsView.$('.cohort-select').val()).toBe('');
                    expect(cohortsView.$('.cohort-management-group-header .title-value').text()).toBe('');
                });

                it('can select a cohort', function () {
                    createCohortsView(this, 1);
                    verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                });

                it('can switch cohort', function () {
                    createCohortsView(this, 1);
                    cohortsView.$('.cohort-select').val("2").change();
                    verifyHeader(2, 'Dog Lovers', dogLoversInitialCount);
                });
            });

            describe("Add Cohorts Form", function () {
                var defaultCohortName = 'New Cohort';

                it("can add a cohort", function() {
                    createCohortsView(this, null, { cohorts: [] });
                    cohortsView.$('.action-create').click();
                    expect(cohortsView.$('.cohort-management-create-form').length).toBe(1);
                    expect(cohortsView.$('.cohort-management-nav')).toHaveClass('is-disabled');
                    expect(cohortsView.$('.cohort-management-group')).toHaveClass('is-hidden');
                    cohortsView.$('.cohort-create-name').val(defaultCohortName);
                    cohortsView.$('.action-save').click();
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/add', 'name=New+Cohort');
                    AjaxHelpers.respondWithJson(
                        requests,
                        {
                            success: true,
                            cohort: { id: 1, name: defaultCohortName }
                        }
                    );
                    AjaxHelpers.respondWithJson(
                        requests,
                        { cohorts: createMockCohort(defaultCohortName) }
                    );
                    verifyMessage(
                        'The ' + defaultCohortName + ' cohort group has been created.' +
                            ' You can manually add students to this group below.',
                        'confirmation'
                    );
                    verifyHeader(1, defaultCohortName, 0);
                    expect(cohortsView.$('.cohort-management-nav')).not.toHaveClass('is-disabled');
                    expect(cohortsView.$('.cohort-management-group')).not.toHaveClass('is-hidden');
                    expect(cohortsView.$('.cohort-management-create-form').length).toBe(0);
                });

                it("trims off whitespace before adding a cohort", function() {
                    createCohortsView(this);
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-create-name').val('  New Cohort   ');
                    cohortsView.$('.action-save').click();
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/add', 'name=New+Cohort');
                });

                it("does not allow a blank cohort name to be submitted", function() {
                    createCohortsView(this, 1);
                    cohortsView.$('.action-create').click();
                    expect(cohortsView.$('.cohort-management-create-form').length).toBe(1);
                    cohortsView.$('.cohort-create-name').val('');
                    expect(cohortsView.$('.cohort-management-nav')).toHaveClass('is-disabled');
                    cohortsView.$('.action-save').click();
                    expect(requests.length).toBe(0);
                    verifyMessage('Please enter a name for your new cohort group.', 'error');
                });

                it("shows a message when adding a cohort throws a server error", function() {
                    createCohortsView(this, 1);
                    cohortsView.$('.action-create').click();
                    expect(cohortsView.$('.cohort-management-create-form').length).toBe(1);
                    cohortsView.$('.cohort-create-name').val(defaultCohortName);
                    cohortsView.$('.action-save').click();
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/add', 'name=New+Cohort');
                    AjaxHelpers.respondWithError(requests);
                    verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                    verifyMessage(
                        "We've encountered an error. Please refresh your browser and then try again.",
                        'error'
                    );
                });

                it("shows a server message if adding a cohort fails", function() {
                    createCohortsView(this, 1);
                    cohortsView.$('.action-create').click();
                    expect(cohortsView.$('.cohort-management-create-form').length).toBe(1);
                    cohortsView.$('.cohort-create-name').val('Cat Lovers');
                    cohortsView.$('.action-save').click();
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/add', 'name=Cat+Lovers');
                    AjaxHelpers.respondWithJson(
                        requests,
                        {
                            success: false,
                            msg: 'You cannot create two cohorts with the same name'
                        }
                    );
                    verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                    verifyMessage('You cannot create two cohorts with the same name', 'error');
                });

                it("is removed when 'Cancel' is clicked", function() {
                    createCohortsView(this, 1);
                    cohortsView.$('.action-create').click();
                    expect(cohortsView.$('.cohort-management-create-form').length).toBe(1);
                    expect(cohortsView.$('.cohort-management-nav')).toHaveClass('is-disabled');
                    cohortsView.$('.action-cancel').click();
                    expect(cohortsView.$('.cohort-management-create-form').length).toBe(0);
                    expect(cohortsView.$('.cohort-management-nav')).not.toHaveClass('is-disabled');
                });

                it("shows an error if canceled when no cohorts are defined", function() {
                    createCohortsView(this, null, { cohorts: [] });
                    cohortsView.$('.action-create').click();
                    expect(cohortsView.$('.cohort-management-create-form').length).toBe(1);
                    expect(cohortsView.$('.cohort-management-nav')).toHaveClass('is-disabled');
                    cohortsView.$('.action-cancel').click();
                    verifyMessage(
                        'You currently have no cohort groups configured',
                        'warning',
                        'Add Cohort Group'
                    );
                });

                it("hides any error message when switching to show a cohort", function() {
                    createCohortsView(this, 1);

                    // First try to save a blank name to create a message
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-create-name').val('');
                    cohortsView.$('.action-save').click();
                    verifyMessage('Please enter a name for your new cohort group.', 'error');

                    // Now switch to a different cohort
                    cohortsView.$('.cohort-select').val("2").change();
                    verifyHeader(2, 'Dog Lovers', dogLoversInitialCount);
                    verifyNoMessage();
                });

                it("hides any error message when canceling the form", function() {
                    createCohortsView(this, 1);

                    // First try to save a blank name to create a message
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-create-name').val('');
                    cohortsView.$('.action-save').click();
                    verifyMessage('Please enter a name for your new cohort group.', 'error');

                    // Now cancel the form
                    cohortsView.$('.action-cancel').click();
                    verifyNoMessage();
                });
            });

            describe("Add Students Button", function () {
                var getStudentInput, addStudents, respondToAdd;

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

                it('shows an error when adding with no students specified', function() {
                    createCohortsView(this, 1);
                    addStudents('    ');
                    expect(requests.length).toBe(0);
                    verifyMessage('Please enter a username or email.', 'error');
                    expect(getStudentInput().val()).toBe('');
                });

                it('can add a single student', function() {
                    var catLoversUpdatedCount = catLoversInitialCount + 1;
                    createCohortsView(this, 1);
                    addStudents('student@sample.com');
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/1/add', 'users=student%40sample.com');
                    respondToAdd({ added: ['student@sample.com'] });
                    respondToRefresh(catLoversUpdatedCount, dogLoversInitialCount);
                    verifyHeader(1, 'Cat Lovers', catLoversUpdatedCount);
                    verifyMessage('1 student has been added to this cohort group', 'confirmation');
                    expect(getStudentInput().val()).toBe('');
                });

                it('shows an error when adding a student that does not exist', function() {
                    createCohortsView(this, 1);
                    addStudents('unknown@sample.com');
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/1/add', 'users=unknown%40sample.com');
                    respondToAdd({ unknown: ['unknown@sample.com'] });
                    respondToRefresh(catLoversInitialCount, dogLoversInitialCount);
                    verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                    verifyDetailedMessage('There was an error when trying to add students:', 'error',
                        [unknownUserMessage('unknown@sample.com')]
                    );
                    expect(getStudentInput().val()).toBe('unknown@sample.com');
                });

                it('shows a "view all" button when more than 5 students do not exist', function() {
                    var sixUsers = 'unknown1@sample.com, unknown2@sample.com, unknown3@sample.com, unknown4@sample.com, unknown5@sample.com, unknown6@sample.com';
                    createCohortsView(this, 1);

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
                    verifyDetailedMessage('There were 6 errors when trying to add students:', 'error',
                        [
                            unknownUserMessage('unknown1@sample.com'), unknownUserMessage('unknown2@sample.com'),
                            unknownUserMessage('unknown3@sample.com'), unknownUserMessage('unknown4@sample.com'),
                            unknownUserMessage('unknown5@sample.com')
                        ],
                        'View all errors'
                    );
                    expect(getStudentInput().val()).toBe(sixUsers);
                    // Click "View all"
                    cohortsView.$('.action-expand').click();
                    verifyDetailedMessage('There were 6 errors when trying to add students:', 'error',
                        [
                            unknownUserMessage('unknown1@sample.com'), unknownUserMessage('unknown2@sample.com'),
                            unknownUserMessage('unknown3@sample.com'), unknownUserMessage('unknown4@sample.com'),
                            unknownUserMessage('unknown5@sample.com'), unknownUserMessage('unknown6@sample.com')
                        ]
                    );
                });

                it('shows students moved from one cohort to another', function() {
                    var sixUsers = 'moved1@sample.com, moved2@sample.com, moved3@sample.com, alreadypresent@sample.com';
                    createCohortsView(this, 1);

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

                    verifyDetailedMessage('3 students have been added to this cohort group', 'confirmation',
                        [
                            "2 students were removed from group 2",
                            "1 student was removed from group 3",
                            "1 student was already in the cohort group"
                        ]
                    );
                    expect(getStudentInput().val()).toBe('');
                });

                it('shows a message when the add fails', function() {
                    createCohortsView(this, 1);
                    addStudents('student@sample.com');
                    AjaxHelpers.respondWithError(requests);
                    verifyMessage('Error adding students.', 'error');
                    expect(getStudentInput().val()).toBe('student@sample.com');
                });

                it('clears an error message on subsequent add', function() {
                    createCohortsView(this, 1);

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
