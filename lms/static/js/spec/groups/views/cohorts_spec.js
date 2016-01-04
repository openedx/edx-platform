define(['backbone', 'jquery', 'common/js/spec_helpers/ajax_helpers', 'common/js/spec_helpers/template_helpers',
        'js/groups/views/cohorts', 'js/groups/collections/cohort', 'js/groups/models/content_group',
        'js/groups/models/course_cohort_settings', 'js/utils/animation', 'js/vendor/jquery.qubit',
        'js/groups/views/course_cohort_settings_notification', 'js/groups/models/cohort_discussions',
        'js/groups/views/cohort_discussions', 'js/groups/views/cohort_discussions_course_wide',
        'js/groups/views/cohort_discussions_inline'
        ],
    function (Backbone, $, AjaxHelpers, TemplateHelpers, CohortsView, CohortCollection, ContentGroupModel,
              CourseCohortSettingsModel, AnimationUtil, Qubit, CourseCohortSettingsNotificationView, DiscussionTopicsSettingsModel,
              CohortDiscussionsView, CohortCourseWideDiscussionsView, CohortInlineDiscussionsView) {
        'use strict';

        describe("Cohorts View", function () {
            var catLoversInitialCount = 123, dogLoversInitialCount = 456, unknownUserMessage,
                createMockCohort, createMockCohorts, createMockContentGroups, createMockCohortSettingsJson,
                createCohortsView, cohortsView, requests, respondToRefresh, verifyMessage, verifyNoMessage,
                verifyDetailedMessage, verifyHeader, expectCohortAddRequest, getAddModal, selectContentGroup,
                clearContentGroup, saveFormAndExpectErrors, createMockCohortSettings, MOCK_COHORTED_USER_PARTITION_ID,
                MOCK_UPLOAD_COHORTS_CSV_URL, MOCK_STUDIO_ADVANCED_SETTINGS_URL, MOCK_STUDIO_GROUP_CONFIGURATIONS_URL,
                MOCK_MANUAL_ASSIGNMENT, MOCK_RANDOM_ASSIGNMENT, createMockCohortDiscussionsJson,
                createMockCohortDiscussions, showAndAssertDiscussionTopics;

            // Selectors
            var discussionsToggle ='.toggle-cohort-management-discussions',
                inlineDiscussionsFormCss = '.cohort-inline-discussions-form',
                courseWideDiscussionsFormCss = '.cohort-course-wide-discussions-form',
                courseWideDiscussionsSaveButtonCss = '.cohort-course-wide-discussions-form .action-save',
                inlineDiscussionsSaveButtonCss = '.cohort-inline-discussions-form .action-save',
                inlineDiscussionsForm, courseWideDiscussionsForm;

            MOCK_MANUAL_ASSIGNMENT = 'manual';
            MOCK_RANDOM_ASSIGNMENT = 'random';
            MOCK_COHORTED_USER_PARTITION_ID = 0;
            MOCK_UPLOAD_COHORTS_CSV_URL = 'http://upload-csv-file-url/';
            MOCK_STUDIO_ADVANCED_SETTINGS_URL = 'http://studio/settings/advanced';
            MOCK_STUDIO_GROUP_CONFIGURATIONS_URL = 'http://studio/group_configurations';

            createMockCohort = function (name, id, userCount, groupId, userPartitionId, assignmentType) {
                return {
                    id: id !== undefined ? id : 1,
                    name: name,
                    assignment_type: assignmentType || MOCK_MANUAL_ASSIGNMENT,
                    user_count: userCount !== undefined ? userCount : 0,
                    group_id: groupId,
                    user_partition_id: userPartitionId
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

            createMockContentGroups = function () {
                return [
                    new ContentGroupModel({
                        id: 0, name: 'Dog Content', user_partition_id: MOCK_COHORTED_USER_PARTITION_ID
                    }),
                    new ContentGroupModel({
                        id: 1, name: 'Cat Content', user_partition_id: MOCK_COHORTED_USER_PARTITION_ID
                    })
                ];
            };

            createMockCohortSettingsJson = function (isCohorted, cohortedInlineDiscussions, cohortedCourseWideDiscussions, alwaysCohortInlineDiscussions) {
                return {
                    id: 0,
                    is_cohorted: isCohorted || false,
                    cohorted_inline_discussions: cohortedInlineDiscussions || [],
                    cohorted_course_wide_discussions: cohortedCourseWideDiscussions || [],
                    always_cohort_inline_discussions: alwaysCohortInlineDiscussions || true
                };
            };

            createMockCohortSettings = function (isCohorted, cohortedInlineDiscussions, cohortedCourseWideDiscussions, alwaysCohortInlineDiscussions) {
                return new CourseCohortSettingsModel(
                    createMockCohortSettingsJson(isCohorted, cohortedInlineDiscussions, cohortedCourseWideDiscussions, alwaysCohortInlineDiscussions)
                );
            };

            createMockCohortDiscussionsJson = function (allCohorted) {
                return {
                    course_wide_discussions: {
                        children: ['Topic_C_1', 'Topic_C_2'],
                        entries: {
                            Topic_C_1: {
                               sort_key: null,
                               is_cohorted: true,
                               id: 'Topic_C_1'
                            },
                            Topic_C_2: {
                                sort_key: null,
                                is_cohorted: false,
                                id: 'Topic_C_2'
                            }
                        }
                    },
                    inline_discussions: {
                        subcategories: {
                            Topic_I_1: {
                                subcategories: {},
                                children: ['Inline_Discussion_1', 'Inline_Discussion_2'],
                                entries: {
                                    Inline_Discussion_1: {
                                        sort_key: null,
                                        is_cohorted: true,
                                        id: 'Inline_Discussion_1'
                                    },
                                    Inline_Discussion_2: {
                                        sort_key: null,
                                        is_cohorted: allCohorted || false,
                                        id: 'Inline_Discussion_2'
                                    }
                                }
                            }
                        },
                        children: ['Topic_I_1']
                    }
                };
            };

            createMockCohortDiscussions = function (allCohorted) {
                return new DiscussionTopicsSettingsModel(
                    createMockCohortDiscussionsJson(allCohorted)
                );
            };

            createCohortsView = function (test, options) {
                var cohortsJson, cohorts, contentGroups, cohortSettings, cohortDiscussions;
                options = options || {};
                cohortsJson = options.cohorts ? {cohorts: options.cohorts} : createMockCohorts();
                cohorts = new CohortCollection(cohortsJson, {parse: true});
                contentGroups = options.contentGroups || createMockContentGroups();
                cohortSettings = options.cohortSettings || createMockCohortSettings(true);
                cohortSettings.url = '/mock_service/cohorts/settings';
                cohorts.url = '/mock_service/cohorts';

                cohortDiscussions = options.cohortDiscussions || createMockCohortDiscussions();
                cohortDiscussions.url = '/mock_service/cohorts/discussion/topics';

                requests = AjaxHelpers.requests(test);
                cohortsView = new CohortsView({
                    model: cohorts,
                    contentGroups: contentGroups,
                    cohortSettings: cohortSettings,
                    context: {
                        discussionTopicsSettingsModel: cohortDiscussions,
                        uploadCohortsCsvUrl: MOCK_UPLOAD_COHORTS_CSV_URL,
                        studioAdvancedSettingsUrl: MOCK_STUDIO_ADVANCED_SETTINGS_URL,
                        studioGroupConfigurationsUrl: MOCK_STUDIO_GROUP_CONFIGURATIONS_URL
                    }
                });

                cohortsView.render();
                if (options && options.selectCohort) {
                    cohortsView.$('.cohort-select').val(options.selectCohort.toString()).change();
                }
            };

            respondToRefresh = function(catCount, dogCount) {
                AjaxHelpers.respondWithJson(requests, createMockCohorts(catCount, dogCount));
            };

            expectCohortAddRequest = function(name, groupId, userPartitionId, assignmentType) {
                AjaxHelpers.expectJsonRequest(
                    requests, 'POST', '/mock_service/cohorts',
                    {
                        name: name,
                        user_count: 0,
                        assignment_type: assignmentType,
                        group_id: groupId,
                        user_partition_id: userPartitionId
                    }
                );
            };

            getAddModal = function() {
                return cohortsView.$('.cohort-management-add-form');
            };

            selectContentGroup = function(groupId, userPartitionId) {
                var ids = groupId + ':' + userPartitionId;
                cohortsView.$('.radio-yes').prop('checked', true).change();
                cohortsView.$('.input-cohort-group-association').val(ids).change();
                expect(cohortsView.$('.input-cohort-group-association').prop('disabled')).toBeFalsy();
            };

            clearContentGroup = function() {
                cohortsView.$('.radio-no').prop('checked', true).change();
                expect(cohortsView.$('.input-cohort-group-association').prop('disabled')).toBeTruthy();
                expect(cohortsView.$('.input-cohort-group-association').val()).toBe('None');
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

            verifyHeader = function(expectedCohortId, expectedTitle, expectedCount, assignmentType) {
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
                assignmentType = assignmentType || MOCK_MANUAL_ASSIGNMENT;
                var manualMessage = "Learners are added to this cohort only when you provide their email addresses " +
                    "or usernames on this page.";
                var randomMessage = "Learners are added to this cohort automatically.";
                var message = (assignmentType == MOCK_MANUAL_ASSIGNMENT) ? manualMessage : randomMessage;
                expect(header.find('.cohort-management-group-setup .setup-value').text().trim().split('\n')[0]).toBe(message);
            };

            saveFormAndExpectErrors = function(action, errors) {
                var form, expectedTitle;
                if (action === 'add') {
                    expectedTitle = 'The cohort cannot be added';
                    form = getAddModal();
                } else {
                    expectedTitle = 'The cohort cannot be saved';
                    form = cohortsView.$('.cohort-management-settings-form');
                }
                form.find('.action-save').click();
                AjaxHelpers.expectNoRequests(requests);
                verifyDetailedMessage(expectedTitle, 'error', errors);
            };

            showAndAssertDiscussionTopics = function(that) {

                createCohortsView(that);

                // Should see the control to toggle cohort discussions.
                expect(cohortsView.$(discussionsToggle)).not.toHaveClass('is-hidden');
                // But discussions form should not be visible until toggle is clicked.
                expect(cohortsView.$(inlineDiscussionsFormCss).length).toBe(0);
                expect(cohortsView.$(courseWideDiscussionsFormCss).length).toBe(0);

                expect(cohortsView.$(discussionsToggle).text()).
                    toContain('Specify whether discussion topics are divided by cohort');

                cohortsView.$(discussionsToggle).click();
                // After toggle is clicked, it should be hidden.
                expect(cohortsView.$(discussionsToggle)).toHaveClass('is-hidden');

                // Should see the course wide discussions form and its content
                courseWideDiscussionsForm = cohortsView.$(courseWideDiscussionsFormCss);
                expect(courseWideDiscussionsForm.length).toBe(1);

                expect(courseWideDiscussionsForm.text()).
                    toContain('Course-Wide Discussion Topics');
                expect(courseWideDiscussionsForm.text()).
                    toContain('Select the course-wide discussion topics that you want to divide by cohort.');

                // Should see the inline discussions form and its content
                inlineDiscussionsForm = cohortsView.$(inlineDiscussionsFormCss);
                expect(inlineDiscussionsForm.length).toBe(1);
                expect(inlineDiscussionsForm.text()).
                    toContain('Content-Specific Discussion Topics');
                expect(inlineDiscussionsForm.text()).
                    toContain('Specify whether content-specific discussion topics are divided by cohort.');
            };

            unknownUserMessage = function (name) {
                return "Unknown user: " +  name;
            };

            beforeEach(function () {
                setFixtures('<ul class="instructor-nav"><li class="nav-item"><<a href data-section="cohort_management" class="active-section">Cohort Management</a></li></ul><div></div><div class="cohort-state-message"></div>');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohorts');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-form');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-selector');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-editor');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-group-header');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/notification');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-state');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-discussions-category');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-discussions-subcategory');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-discussions-course-wide');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-discussions-inline');
                TemplateHelpers.installTemplate('templates/file-upload');
            });

            it("shows an error if no cohorts are defined", function() {
                createCohortsView(this, {cohorts: []});
                verifyMessage(
                    'You currently have no cohorts configured',
                    'warning',
                    'Add Cohort'
                );

                // If no cohorts have been created, can't upload a CSV file.
                expect(cohortsView.$('.wrapper-cohort-supplemental')).toHaveClass('is-hidden');
                // if no cohorts have been created, can't show the link to discussion topics.
                expect(cohortsView.$('.cohort-discussions-nav')).toHaveClass('is-hidden');
            });

            it("syncs data when membership tab is clicked", function() {
                createCohortsView(this, {selectCohort: 1});
                verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                $(cohortsView.getSectionCss("cohort_management")).click();
                AjaxHelpers.expectRequest(requests, 'GET', '/mock_service/cohorts');
                respondToRefresh(1001, 2);
                verifyHeader(1, 'Cat Lovers', 1001);
            });

            it('can upload a CSV of cohort assignments if a cohort exists', function () {
                var uploadCsvToggle, fileUploadForm, fileUploadFormCss='#file-upload-form';

                createCohortsView(this);

                // Should see the control to toggle CSV file upload.
                expect(cohortsView.$('.wrapper-cohort-supplemental')).not.toHaveClass('is-hidden');
                // But upload form should not be visible until toggle is clicked.
                expect(cohortsView.$(fileUploadFormCss).length).toBe(0);
                uploadCsvToggle = cohortsView.$('.toggle-cohort-management-secondary');
                expect(uploadCsvToggle.text()).
                    toContain('Assign students to cohorts by uploading a CSV file');
                uploadCsvToggle.click();
                // After toggle is clicked, it should be hidden.
                expect(uploadCsvToggle).toHaveClass('is-hidden');

                fileUploadForm = cohortsView.$(fileUploadFormCss);
                expect(fileUploadForm.length).toBe(1);
                cohortsView.$(fileUploadForm).fileupload('add', {files: [{name: 'upload_file.txt'}]});
                cohortsView.$('.submit-file-button').click();

                // No file will actually be uploaded because "uploaded_file.txt" doesn't actually exist.
                AjaxHelpers.expectRequest(requests, 'POST', MOCK_UPLOAD_COHORTS_CSV_URL, new FormData());
                AjaxHelpers.respondWithJson(requests, {});
                expect(cohortsView.$('.file-upload-form-result .message-confirmation .message-title').text().trim())
                    .toBe("Your file 'upload_file.txt' has been uploaded. Allow a few minutes for processing.");
            });

            it('can show discussion topics if cohort exists', function () {
                showAndAssertDiscussionTopics(this);
            });

            describe("Cohort Selector", function () {
                it('has no initial selection', function () {
                    createCohortsView(this);
                    expect(cohortsView.$('.cohort-select').val()).toBe('');
                    expect(cohortsView.$('.cohort-management-group-header .title-value').text()).toBe('');
                });

                it('can select a cohort', function () {
                    createCohortsView(this, {selectCohort: 1});
                    verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                });

                it('can switch cohort', function () {
                    createCohortsView(this, {selectCohort: 1});
                    cohortsView.$('.cohort-select').val('2').change();
                    verifyHeader(2, 'Dog Lovers', dogLoversInitialCount);
                });
            });

            describe("Course Cohort Settings", function () {
                it('can enable and disable cohorting', function () {
                    createCohortsView(this, {cohortSettings: createMockCohortSettings(false)});

                    expect(cohortsView.$('.cohorts-state').prop('checked')).toBeFalsy();

                    cohortsView.$('.cohorts-state').prop('checked', true).change();
                    AjaxHelpers.expectJsonRequest(
                        requests, 'PATCH', '/mock_service/cohorts/settings',
                        {is_cohorted: true}
                    );
                    AjaxHelpers.respondWithJson(
                        requests,
                        {is_cohorted: true}
                    );
                    expect(cohortsView.$('.cohorts-state').prop('checked')).toBeTruthy();

                    cohortsView.$('.cohorts-state').prop('checked', false).change();
                    AjaxHelpers.expectJsonRequest(
                        requests, 'PATCH', '/mock_service/cohorts/settings',
                        {is_cohorted: false}
                    );
                    AjaxHelpers.respondWithJson(
                        requests,
                        {is_cohorted: false}
                    );
                    expect(cohortsView.$('.cohorts-state').prop('checked')).toBeFalsy();
                });


                it('shows an appropriate cohort status message', function () {
                     var createCourseCohortSettingsNotificationView = function (is_cohorted) {
                        var notificationView = new CourseCohortSettingsNotificationView({
                            el: $('.cohort-state-message'),
                            cohortEnabled: is_cohorted});
                        notificationView.render();
                        return notificationView;
                     };

                    var notificationView = createCourseCohortSettingsNotificationView(true);
                    expect(notificationView.$('.action-toggle-message').text().trim()).toBe('Cohorts Enabled');

                    notificationView = createCourseCohortSettingsNotificationView(false);
                    expect(notificationView.$('.action-toggle-message').text().trim()).toBe('Cohorts Disabled');
                });

                it('shows an appropriate error message for HTTP500', function () {
                    createCohortsView(this, {cohortSettings: createMockCohortSettings(false)});
                    expect(cohortsView.$('.cohorts-state').prop('checked')).toBeFalsy();
                    cohortsView.$('.cohorts-state').prop('checked', true).change();
                    AjaxHelpers.respondWithError(requests, 500);
                    var expectedTitle = "We've encountered an error. Refresh your browser and then try again."
                    expect(cohortsView.$('.message-title').text().trim()).toBe(expectedTitle);
                });
            });

            describe("Cohort Group Header", function () {
                it("renders header correctly", function () {
                    var cohortName = 'Transformers',
                        newCohortName = 'X Men';
                    var expectedRequest = function(assignment_type) {
                        return {
                            name: newCohortName,
                            assignment_type: assignment_type,
                            group_id: null,
                            user_partition_id: null
                        }
                    };
                    createCohortsView(this, {
                        cohorts: [
                            {
                                id: 1,
                                name: cohortName,
                                assignment_type: MOCK_RANDOM_ASSIGNMENT,
                                group_id: 111,
                                user_partition_id: MOCK_COHORTED_USER_PARTITION_ID
                            }
                        ],
                        selectCohort: 1
                    });

                    // Select settings tab
                    cohortsView.$('.tab-settings a').click();

                    verifyHeader(1, cohortName, 0, MOCK_RANDOM_ASSIGNMENT);

                    // Update existing cohort values
                    cohortsView.$('.cohort-name').val(newCohortName);
                    cohortsView.$('.type-manual').prop('checked', true).change();
                    clearContentGroup();

                    // Save the updated settings
                    cohortsView.$('.action-save').click();
                    AjaxHelpers.expectJsonRequest(
                        requests, 'PATCH', '/mock_service/cohorts/1',
                        expectedRequest(MOCK_MANUAL_ASSIGNMENT)
                    );
                    AjaxHelpers.respondWithJson(
                        requests,
                        createMockCohort(newCohortName, 1, 0, null, null)
                    );

                    verifyHeader(1, newCohortName, 0, MOCK_MANUAL_ASSIGNMENT);
                });
            });

            describe("Cohort Editor Tab Panel", function () {
                it("initially selects the Manage Students tab", function () {
                    createCohortsView(this, {selectCohort: 1});
                    expect(cohortsView.$('.tab-manage_students')).toHaveClass('is-selected');
                    expect(cohortsView.$('.tab-settings')).not.toHaveClass('is-selected');
                    expect(cohortsView.$('.tab-content-manage_students')).not.toHaveClass('is-hidden');
                    expect(cohortsView.$('.tab-content-settings')).toHaveClass('is-hidden');
                });

                it("can select the Settings tab", function () {
                    createCohortsView(this, {selectCohort: 1});
                    cohortsView.$('.tab-settings a').click();
                    expect(cohortsView.$('.tab-manage_students')).not.toHaveClass('is-selected');
                    expect(cohortsView.$('.tab-settings')).toHaveClass('is-selected');
                    expect(cohortsView.$('.tab-content-manage_students')).toHaveClass('is-hidden');
                    expect(cohortsView.$('.tab-content-settings')).not.toHaveClass('is-hidden');
                });
            });

            describe("Add Cohorts Form", function () {
                var defaultCohortName = 'New Cohort';
                var assignmentType = 'random';

                it("can add a cohort", function() {
                    var contentGroupId = 0,
                        contentGroupUserPartitionId = 0;
                    createCohortsView(this, {cohorts: []});
                    cohortsView.$('.action-create').click();
                    expect(cohortsView.$('.cohort-management-settings-form').length).toBe(1);
                    expect(cohortsView.$('.cohort-management-nav')).toHaveClass('is-disabled');
                    expect(cohortsView.$('.cohort-management-group')).toHaveClass('is-hidden');
                    cohortsView.$('.cohort-name').val(defaultCohortName);
                    cohortsView.$('.type-random').prop('checked', true).change();
                    selectContentGroup(contentGroupId, MOCK_COHORTED_USER_PARTITION_ID);
                    cohortsView.$('.action-save').click();
                    expectCohortAddRequest(defaultCohortName, contentGroupId, MOCK_COHORTED_USER_PARTITION_ID, assignmentType);
                    AjaxHelpers.respondWithJson(
                        requests,
                        {
                            id: 1,
                            name: defaultCohortName,
                            assignment_type: assignmentType,
                            group_id: contentGroupId,
                            user_partition_id: MOCK_COHORTED_USER_PARTITION_ID
                        }
                    );
                    AjaxHelpers.respondWithJson(
                        requests,
                        { cohorts: createMockCohort(defaultCohortName, 1, 0, null, null, assignmentType) }
                    );
                    verifyMessage(
                        'The ' + defaultCohortName + ' cohort has been created.' +
                            ' You can manually add students to this cohort below.',
                        'confirmation'
                    );
                    verifyHeader(1, defaultCohortName, 0, MOCK_RANDOM_ASSIGNMENT);
                    expect(cohortsView.$('.cohort-management-nav')).not.toHaveClass('is-disabled');
                    expect(cohortsView.$('.cohort-management-group')).not.toHaveClass('is-hidden');
                    expect(getAddModal().find('.cohort-management-settings-form').length).toBe(0);
                });

                it("has default assignment type set to manual", function() {
                    var cohortName = "iCohort";
                    createCohortsView(this, {cohorts: []});
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-name').val(cohortName);
                    cohortsView.$('.action-save').click();
                    expectCohortAddRequest(cohortName, null, null, MOCK_MANUAL_ASSIGNMENT);
                    AjaxHelpers.respondWithJson(
                        requests,
                        {
                            id: 1,
                            name: cohortName,
                            assignment_type: MOCK_MANUAL_ASSIGNMENT,
                            group_id: null,
                            user_partition_id: null
                        }
                    );
                    AjaxHelpers.respondWithJson(
                        requests,
                        { cohorts: createMockCohort(cohortName, 1, 0, null, null, MOCK_MANUAL_ASSIGNMENT) }
                    );
                    verifyHeader(1, cohortName, 0, MOCK_MANUAL_ASSIGNMENT);
                });

                it("trims off whitespace before adding a cohort", function() {
                    createCohortsView(this);
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-name').val('  New Cohort   ');
                    cohortsView.$('.action-save').click();
                    expectCohortAddRequest('New Cohort', null, null, MOCK_MANUAL_ASSIGNMENT);
                });

                it("does not allow a blank cohort name to be submitted", function() {
                    createCohortsView(this, {selectCohort: 1});
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-name').val('  ');
                    saveFormAndExpectErrors('add', ['You must specify a name for the cohort']);
                });

                it("shows a message saving when choosing to have content groups but not selecting one", function() {
                    createCohortsView(this, {selectCohort: 1});
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-name').val('New Cohort');
                    cohortsView.$('.radio-yes').prop('checked', true).change();
                    saveFormAndExpectErrors('add', ['You did not select a content group']);
                });

                it("shows two message when both fields have problems", function() {
                    createCohortsView(this, {selectCohort: 1});
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-name').val('');
                    cohortsView.$('.radio-yes').prop('checked', true).change();
                    saveFormAndExpectErrors('add', [
                        'You must specify a name for the cohort',
                        'You did not select a content group'
                    ]);
                });

                it("shows a message when adding a cohort returns a server error", function() {
                    var addModal;
                    createCohortsView(this, {selectCohort: 1});
                    cohortsView.$('.action-create').click();
                    addModal = getAddModal();
                    expect(addModal.find('.cohort-management-settings-form').length).toBe(1);
                    addModal.find('.cohort-name').val(defaultCohortName);
                    addModal.find('.action-save').click();
                    AjaxHelpers.respondWithError(requests, 400, {
                        error: 'You cannot add two cohorts with the same name'
                    });
                    verifyHeader(1, 'Cat Lovers', catLoversInitialCount);
                    verifyMessage(
                        'You cannot add two cohorts with the same name',
                        'error'
                    );
                });

                it("is removed when 'Cancel' is clicked", function() {
                    createCohortsView(this, {selectCohort: 1});
                    cohortsView.$('.action-create').click();
                    expect(getAddModal().find('.cohort-management-settings-form').length).toBe(1);
                    expect(cohortsView.$('.cohort-management-nav')).toHaveClass('is-disabled');
                    cohortsView.$('.action-cancel').click();
                    expect(getAddModal().find('.cohort-management-settings-form').length).toBe(0);
                    expect(cohortsView.$('.cohort-management-nav')).not.toHaveClass('is-disabled');
                });

                it("shows an error if canceled when no cohorts are defined", function() {
                    createCohortsView(this, {cohorts: []});
                    cohortsView.$('.action-create').click();
                    expect(getAddModal().find('.cohort-management-settings-form').length).toBe(1);
                    expect(cohortsView.$('.cohort-management-nav')).toHaveClass('is-disabled');
                    cohortsView.$('.action-cancel').click();
                    verifyMessage(
                        'You currently have no cohorts configured',
                        'warning',
                        'Add Cohort'
                    );
                });

                it("hides any error message when switching to show a cohort", function() {
                    createCohortsView(this, {selectCohort: 1});

                    // First try to save a blank name to create a message
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-name').val('');
                    saveFormAndExpectErrors('add', ['You must specify a name for the cohort']);

                    // Now switch to a different cohort
                    cohortsView.$('.cohort-select').val('2').change();
                    verifyHeader(2, 'Dog Lovers', dogLoversInitialCount);
                    verifyNoMessage();
                });

                it("hides any error message when canceling the form", function() {
                    createCohortsView(this, {selectCohort: 1});

                    // First try to save a blank name to create a message
                    cohortsView.$('.action-create').click();
                    cohortsView.$('.cohort-name').val('');
                    saveFormAndExpectErrors('add', ['You must specify a name for the cohort']);

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
                    createCohortsView(this, {selectCohort: 1});
                    addStudents('    ');
                    AjaxHelpers.expectNoRequests(requests);
                    verifyMessage('Enter a username or email.', 'error');
                    expect(getStudentInput().val()).toBe('');
                });

                it('can add a single student', function() {
                    var catLoversUpdatedCount = catLoversInitialCount + 1;
                    createCohortsView(this, {selectCohort: 1});
                    addStudents('student@sample.com');
                    respondToAdd({ added: ['student@sample.com'] });
                    respondToRefresh(catLoversUpdatedCount, dogLoversInitialCount);
                    verifyHeader(1, 'Cat Lovers', catLoversUpdatedCount);
                    verifyMessage('1 student has been added to this cohort', 'confirmation');
                    expect(getStudentInput().val()).toBe('');
                });

                it('shows an error when adding a student that does not exist', function() {
                    createCohortsView(this, {selectCohort: 1});
                    addStudents('unknown@sample.com');
                    AjaxHelpers.expectRequest(
                        requests, 'POST', '/mock_service/cohorts/1/add', 'users=unknown%40sample.com'
                    );
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
                    createCohortsView(this, {selectCohort: 1});

                    addStudents(sixUsers);
                    AjaxHelpers.expectRequest(
                        requests, 'POST', '/mock_service/cohorts/1/add',
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
                    createCohortsView(this, {selectCohort: 1});

                    addStudents(sixUsers);
                    AjaxHelpers.expectRequest(requests, 'POST', '/mock_service/cohorts/1/add',
                            'users=' + sixUsers.replace(/@/g, "%40").replace(/, /g, "%2C+")
                    );
                    respondToAdd({
                        changed: [
                            {email: 'moved1@sample.com', name: 'moved1', previous_cohort: 'cohort 2', username: 'moved1'},
                            {email: 'moved2@sample.com', name: 'moved2', previous_cohort: 'cohort 2', username: 'moved2'},
                            {email: 'moved3@sample.com', name: 'moved3', previous_cohort: 'cohort 3', username: 'moved3'}
                        ],
                        present: ['alreadypresent@sample.com']
                    });
                    respondToRefresh();

                    verifyDetailedMessage('3 students have been added to this cohort', 'confirmation',
                        [
                            "2 students were removed from cohort 2",
                            "1 student was removed from cohort 3",
                            "1 student was already in the cohort"
                        ]
                    );
                    expect(getStudentInput().val()).toBe('');
                });

                it('shows a message when the add fails', function() {
                    createCohortsView(this, {selectCohort: 1});
                    addStudents('student@sample.com');
                    AjaxHelpers.respondWithError(requests);
                    verifyMessage('Error adding students.', 'error');
                    expect(getStudentInput().val()).toBe('student@sample.com');
                });

                it('clears an error message on subsequent add', function() {
                    createCohortsView(this, {selectCohort: 1});

                    // First verify that an error is shown
                    addStudents('student@sample.com');
                    AjaxHelpers.respondWithError(requests);
                    verifyMessage('Error adding students.', 'error');

                    // Now verify that the error is removed on a subsequent add
                    addStudents('student@sample.com');
                    respondToAdd({ added: ['student@sample.com'] });
                    respondToRefresh(catLoversInitialCount + 1, dogLoversInitialCount);
                    verifyMessage('1 student has been added to this cohort', 'confirmation');
                });
            });

            describe("Cohort Settings", function() {
                describe("Content Group Setting", function() {
                    var createCohortsViewWithDeletedContentGroup;

                    createCohortsViewWithDeletedContentGroup = function(test) {
                        createCohortsView(test, {
                            cohorts: [
                                {
                                    id: 1,
                                    name: 'Cat Lovers',
                                    assignment_type: MOCK_RANDOM_ASSIGNMENT,
                                    group_id: 999,
                                    user_partition_id: MOCK_COHORTED_USER_PARTITION_ID
                                }
                            ],
                            selectCohort: 1
                        });
                    };

                    it("shows a select element with an option for each content group", function () {
                        var options;
                        createCohortsView(this, {selectCohort: 1});
                        cohortsView.$('.tab-settings a').click();
                        expect(cohortsView.$('.input-cohort-group-association').prop('disabled')).toBeTruthy();
                        options = cohortsView.$('.input-cohort-group-association option');
                        expect(options.length).toBe(3);
                        expect($(options[0]).text().trim()).toBe('Not selected');
                        expect($(options[1]).text().trim()).toBe('Cat Content');
                        expect($(options[2]).text().trim()).toBe('Dog Content');
                    });

                    it("can select a single content group", function () {
                        createCohortsView(this, {selectCohort: 1});
                        cohortsView.$('.tab-settings a').click();

                        // Select the content group with id 1 and verify the radio button was switched to 'Yes'
                        selectContentGroup(0, MOCK_COHORTED_USER_PARTITION_ID);
                        expect(cohortsView.$('.radio-yes').prop('checked')).toBeTruthy();

                        // Click the save button and verify that the correct request is sent
                        cohortsView.$('.action-save').click();
                        AjaxHelpers.expectJsonRequest(
                            requests, 'PATCH', '/mock_service/cohorts/1',
                            {
                                name: 'Cat Lovers',
                                assignment_type: MOCK_MANUAL_ASSIGNMENT,
                                group_id: 0,
                                user_partition_id: MOCK_COHORTED_USER_PARTITION_ID
                            }
                        );
                        AjaxHelpers.respondWithJson(
                            requests,
                            createMockCohort('Cat Lovers', 1, catLoversInitialCount, 0, 0)
                        );
                        verifyMessage('Saved cohort', 'confirmation');
                    });

                    it("can clear selected content group", function () {
                        createCohortsView(this, {
                            cohorts: [
                                {id: 1, name: 'Cat Lovers', group_id: 0, 'assignment_type': MOCK_MANUAL_ASSIGNMENT}
                            ],
                            selectCohort: 1
                        });
                        cohortsView.$('.tab-settings a').click();
                        expect(cohortsView.$('.radio-yes').prop('checked')).toBeTruthy();
                        clearContentGroup();

                        // Click the save button and verify that the correct request is sent
                        cohortsView.$('.action-save').click();
                        AjaxHelpers.expectJsonRequest(
                            requests, 'PATCH', '/mock_service/cohorts/1',
                            {
                                name: 'Cat Lovers',
                                'assignment_type': MOCK_MANUAL_ASSIGNMENT,
                                group_id: null,
                                user_partition_id: null
                            }
                        );
                        AjaxHelpers.respondWithJson(
                            requests,
                            createMockCohort('Cat Lovers', 1, catLoversInitialCount, 0, 0)
                        );
                        verifyMessage('Saved cohort', 'confirmation');
                    });

                    it("shows a message saving when choosing to have content groups but not selecting one", function() {
                        createCohortsView(this, {selectCohort: 1});
                        cohortsView.$('.tab-settings a').click();
                        cohortsView.$('.cohort-name').val('New Cohort');
                        cohortsView.$('.radio-yes').prop('checked', true).change();
                        saveFormAndExpectErrors('update', ['You did not select a content group']);
                    });

                    it("shows a message when the selected content group does not exist", function () {
                        createCohortsViewWithDeletedContentGroup(this);
                        cohortsView.$('.tab-settings a').click();
                        expect(cohortsView.$('option.option-unavailable').text().trim()).toBe('Deleted Content Group');
                        expect(cohortsView.$('.cohort-management-details-association-course .copy-error').text().trim()).toBe(
                            'Warning: The previously selected content group was deleted. Select another content group.'
                        );
                    });

                    it("can clear a selected content group which had been deleted", function () {
                        createCohortsViewWithDeletedContentGroup(this);
                        cohortsView.$('.tab-settings a').click();
                        expect(cohortsView.$('.radio-yes').prop('checked')).toBeTruthy();
                        clearContentGroup();

                        // Click the save button and verify that the correct request is sent
                        cohortsView.$('.action-save').click();
                        AjaxHelpers.respondWithJson(
                            requests,
                            createMockCohort('Cat Lovers', 1, catLoversInitialCount, 0, 0, MOCK_RANDOM_ASSIGNMENT)
                        );
                        verifyMessage('Saved cohort', 'confirmation');

                        // Verify that the deleted content group and associated message have been removed
                        expect(cohortsView.$('option.option-unavailable').text().trim()).toBe('');
                        expect(cohortsView.$('.cohort-management-details-association-course .copy-error').text().trim()).toBe('');
                    });

                    it("shows an error when saving with a deleted content group", function () {
                        createCohortsViewWithDeletedContentGroup(this);
                        cohortsView.$('.tab-settings a').click();
                        saveFormAndExpectErrors('save', ['The selected content group does not exist']);
                    });

                    it("shows an error when the save fails", function () {
                        createCohortsView(this, {selectCohort: 1});
                        cohortsView.$('.tab-settings a').click();
                        cohortsView.$('.action-save').click();
                        AjaxHelpers.respondWithError(requests);
                        verifyMessage(
                            'We\'ve encountered an error. Refresh your browser and then try again.',
                            'error'
                        );
                    });

                    it("shows an error message when no content groups are specified", function () {
                        var message;
                        createCohortsView(this, {selectCohort: 1, contentGroups: []});
                        cohortsView.$('.tab-settings a').click();
                        expect(cohortsView.$('.radio-yes').prop('disabled')).toBeTruthy();
                        message = cohortsView.$('.msg-inline').text().trim();
                        expect(message).toContain('Warning: No content groups exist.');
                        expect(message).toContain('Create a content group');
                        expect(
                            cohortsView.$('.msg-inline a').attr('href'),
                            MOCK_STUDIO_GROUP_CONFIGURATIONS_URL
                        );
                    });

                    it("can update existing cohort settings", function () {
                        var cohortName = 'Transformers',
                            newCohortName = 'X Men';
                        var expectedRequest = function(assignment_type) {
                            return {
                                name: newCohortName,
                                assignment_type: assignment_type,
                                group_id: null,
                                user_partition_id: null
                            }
                        };
                        createCohortsView(this, {
                            cohorts: [
                                {
                                    id: 1,
                                    name: cohortName,
                                    assignment_type: MOCK_RANDOM_ASSIGNMENT,
                                    group_id: 111,
                                    user_partition_id: MOCK_COHORTED_USER_PARTITION_ID
                                }
                            ],
                            selectCohort: 1
                        });

                        // Select settings tab
                        cohortsView.$('.tab-settings a').click();

                        // Verify the existing cohort values
                        expect(cohortsView.$('.cohort-name').val()).toBe(cohortName);
                        expect(cohortsView.$('input[name="cohort-assignment-type"]:checked').val()).toBe(MOCK_RANDOM_ASSIGNMENT);
                        expect(cohortsView.$('.radio-yes').prop('checked')).toBeTruthy();

                        // Update existing cohort values
                        cohortsView.$('.cohort-name').val(newCohortName);
                        cohortsView.$('.type-manual').prop('checked', true).change();
                        clearContentGroup();

                        // Save the updated settings
                        cohortsView.$('.action-save').click();
                        AjaxHelpers.expectJsonRequest(
                            requests, 'PATCH', '/mock_service/cohorts/1',
                            expectedRequest(MOCK_MANUAL_ASSIGNMENT)
                        );
                        AjaxHelpers.respondWithJson(
                            requests,
                            createMockCohort(newCohortName, 1, 0, null, null)
                        );

                        // Verify the new/updated cohort values
                        expect(cohortsView.$('.cohort-name').val()).toBe(newCohortName);
                        expect(cohortsView.$('input[name="cohort-assignment-type"]:checked').val()).toBe(MOCK_MANUAL_ASSIGNMENT);
                        expect(cohortsView.$('.radio-no').prop('checked')).toBeTruthy();

                        verifyMessage('Saved cohort', 'confirmation');

                        // Now try to update existing cohort name with an empty name
                        // We can't save a cohort with empty name, so we should see an error message
                        cohortsView.$('.cohort-name').val('');

                        saveFormAndExpectErrors('update', ['You must specify a name for the cohort']);
                    });

                    it("assignment settings are disabled for default cohort", function() {
                        createCohortsView(this, {
                            cohorts: [
                                {
                                    id: 1,
                                    name: 'Cohort.me',
                                    assignment_type: MOCK_RANDOM_ASSIGNMENT,
                                    group_id: 111,
                                    user_partition_id: MOCK_COHORTED_USER_PARTITION_ID
                                }
                            ],
                            selectCohort: 1
                        });

                        // We have a single random cohort so we should not be allowed to change it assignment type
                        expect(cohortsView.$('.cohort-management-assignment-type-settings')).toHaveClass('is-disabled');
                        expect(cohortsView.$('.copy-error').text()).toContain("There must be one cohort to which students can automatically be assigned.");
                    });

                    it("cancel settings works", function() {
                        createCohortsView(this, {selectCohort: 1, contentGroups: []});
                        cohortsView.$('.tab-settings a').click();
                        cohortsView.$('.cohort-name').val('One Two Three');
                        cohortsView.$('.action-cancel').click();
                        expect(cohortsView.$('.tab-manage_students')).toHaveClass('is-selected');
                        expect(cohortsView.$('.tab-settings')).not.toHaveClass('is-selected');
                    });
                });
            });

            describe("Discussion Topics", function() {
                var createCourseWideView, createInlineView,
                    inlineView, courseWideView, assertCohortedTopics;

                createCourseWideView = function(that) {
                    createCohortsView(that);

                    courseWideView = new CohortCourseWideDiscussionsView({
                        el: cohortsView.$('.cohort-discussions-nav').removeClass('is-hidden'),
                        model: cohortsView.context.discussionTopicsSettingsModel,
                        cohortSettings: cohortsView.cohortSettings
                    });
                    courseWideView.render();
                };

                createInlineView = function(that, discussionTopicsSettingsModel) {
                    createCohortsView(that);

                    inlineView = new CohortInlineDiscussionsView({
                        el: cohortsView.$('.cohort-discussions-nav').removeClass('is-hidden'),
                        model: discussionTopicsSettingsModel || cohortsView.context.discussionTopicsSettingsModel,
                        cohortSettings: cohortsView.cohortSettings
                    });
                    inlineView.render();
                };

                assertCohortedTopics = function(view, type) {
                    expect(view.$('.check-discussion-subcategory-' + type).length).toBe(2);
                    expect(view.$('.check-discussion-subcategory-' + type + ':checked').length).toBe(1);
                };

                it('renders the view properly', function() {
                    showAndAssertDiscussionTopics(this);
                });

                describe("Course Wide", function() {

                    it('shows the "Save" button as disabled initially', function() {
                        createCourseWideView(this);
                        expect(courseWideView.$(courseWideDiscussionsSaveButtonCss).prop('disabled')).toBeTruthy();
                    });

                    it('has one cohorted and one non-cohorted topic', function() {
                        createCourseWideView(this);

                        assertCohortedTopics(courseWideView, 'course-wide');

                        expect(courseWideView.$('.cohorted-text').length).toBe(2);
                        expect(courseWideView.$('.cohorted-text.hidden').length).toBe(1);
                    });

                    it('enables the "Save" button after changing checkbox', function() {
                        createCourseWideView(this);

                        // save button is disabled.
                        expect(courseWideView.$(courseWideDiscussionsSaveButtonCss).prop('disabled')).toBeTruthy();

                        $(courseWideView.$('.check-discussion-subcategory-course-wide')[0]).prop('checked', false).change();

                        // save button is enabled.
                        expect(courseWideView.$(courseWideDiscussionsSaveButtonCss).prop('disabled')).toBeFalsy();
                    });

                    it('saves the topic successfully', function() {
                        createCourseWideView(this);

                        $(courseWideView.$('.check-discussion-subcategory-course-wide')[1]).prop('checked', 'checked').change();
                        expect(courseWideView.$(courseWideDiscussionsSaveButtonCss).prop('disabled')).toBeFalsy();

                        // Save the updated settings
                        courseWideView.$('.action-save').click();

                        // fake requests for cohort settings with PATCH method.
                        AjaxHelpers.expectJsonRequest(
                            requests, 'PATCH', '/mock_service/cohorts/settings',
                            {cohorted_course_wide_discussions: ['Topic_C_1', 'Topic_C_2']}
                        );
                        AjaxHelpers.respondWithJson(
                            requests,
                            {cohorted_course_wide_discussions: ['Topic_C_1', 'Topic_C_2']}
                        );

                        // fake request for discussion/topics with GET method.
                        AjaxHelpers.expectJsonRequest(
                            requests, 'GET', '/mock_service/cohorts/discussion/topics'
                        );
                        AjaxHelpers.respondWithJson(
                            requests,
                            createMockCohortDiscussions()
                        );

                        // verify the success message.
                        expect(courseWideView.$(courseWideDiscussionsSaveButtonCss).prop('disabled')).toBeTruthy();
                        verifyMessage('Your changes have been saved.', 'confirmation');
                    });

                    it('shows an appropriate message when subsequent "GET" returns HTTP500', function() {
                        createCourseWideView(this);

                        $(courseWideView.$('.check-discussion-subcategory-course-wide')[1]).prop('checked', 'checked').change();
                        expect(courseWideView.$(courseWideDiscussionsSaveButtonCss).prop('disabled')).toBeFalsy();

                        // Save the updated settings
                        courseWideView.$('.action-save').click();

                        // fake requests for cohort settings with PATCH method.
                        AjaxHelpers.expectJsonRequest(
                            requests, 'PATCH', '/mock_service/cohorts/settings',
                            {cohorted_course_wide_discussions: ['Topic_C_1', 'Topic_C_2']}
                        );
                        AjaxHelpers.respondWithJson(
                            requests,
                            {cohorted_course_wide_discussions: ['Topic_C_1', 'Topic_C_2']}
                        );

                        // fake request for discussion/topics with GET method.
                        AjaxHelpers.expectJsonRequest(
                            requests, 'GET', '/mock_service/cohorts/discussion/topics'
                        );
                        AjaxHelpers.respondWithError(requests, 500);

                        var expectedTitle = "We've encountered an error. Refresh your browser and then try again.";
                        expect(courseWideView.$('.message-title').text().trim()).toBe(expectedTitle);
                    });

                    it('shows an appropriate error message for HTTP500', function () {
                        createCourseWideView(this);

                        $(courseWideView.$('.check-discussion-subcategory-course-wide')[1]).prop('checked', 'checked').change();
                        courseWideView.$('.action-save').click();

                        AjaxHelpers.respondWithError(requests, 500);
                        var expectedTitle = "We've encountered an error. Refresh your browser and then try again.";
                        expect(courseWideView.$('.message-title').text().trim()).toBe(expectedTitle);
                    });
                });

                describe("Inline", function() {
                    var enableSaveButton, mockGetRequest, verifySuccess, mockPatchRequest;

                    enableSaveButton = function() {
                        // enable the inline discussion topics.
                        inlineView.$('.check-cohort-inline-discussions').prop('checked', 'checked').change();

                        $(inlineView.$('.check-discussion-subcategory-inline')[0]).prop('checked', 'checked').change();

                        expect(inlineView.$(inlineDiscussionsSaveButtonCss).prop('disabled')).toBeFalsy();
                    };

                    verifySuccess = function() {
                        // verify the success message.
                        expect(inlineView.$(inlineDiscussionsSaveButtonCss).prop('disabled')).toBeTruthy();
                        verifyMessage('Your changes have been saved.', 'confirmation');
                    };

                    mockPatchRequest = function(cohortedInlineDiscussions) {
                        AjaxHelpers.expectJsonRequest(
                            requests, 'PATCH', '/mock_service/cohorts/settings',
                            {
                                cohorted_inline_discussions: cohortedInlineDiscussions,
                                always_cohort_inline_discussions: false
                            }
                        );
                        AjaxHelpers.respondWithJson(
                            requests,
                            {
                                cohorted_inline_discussions: cohortedInlineDiscussions,
                                always_cohort_inline_discussions: false
                            }
                        );
                    };

                    mockGetRequest = function(allCohorted) {
                        // fake request for discussion/topics with GET method.
                        AjaxHelpers.expectJsonRequest(
                            requests, 'GET', '/mock_service/cohorts/discussion/topics'
                        );
                        AjaxHelpers.respondWithJson(
                            requests,
                            createMockCohortDiscussions(allCohorted)
                        );
                    };

                    it('shows the "Save" button as disabled initially', function() {
                        createInlineView(this);
                        expect(inlineView.$(inlineDiscussionsSaveButtonCss).prop('disabled')).toBeTruthy();
                    });

                    it('shows always cohort radio button as selected', function() {
                        createInlineView(this);
                        inlineView.$('.check-all-inline-discussions').prop('checked', 'checked').change();

                        // verify always cohort inline discussions is being selected.
                        expect(inlineView.$('.check-all-inline-discussions').prop('checked')).toBeTruthy();

                        // verify that inline topics are disabled
                        expect(inlineView.$('.check-discussion-subcategory-inline').prop('disabled')).toBeTruthy();
                        expect(inlineView.$('.check-discussion-category').prop('disabled')).toBeTruthy();

                        // verify that cohort some topics are not being selected.
                        expect(inlineView.$('.check-cohort-inline-discussions').prop('checked')).toBeFalsy();
                    });

                    it('shows cohort some topics radio button as selected', function() {
                        createInlineView(this);
                        inlineView.$('.check-cohort-inline-discussions').prop('checked', 'checked').change();

                        // verify some cohort inline discussions radio is being selected.
                        expect(inlineView.$('.check-cohort-inline-discussions').prop('checked')).toBeTruthy();

                        // verify always cohort radio is not selected.
                        expect(inlineView.$('.check-all-inline-discussions').prop('checked')).toBeFalsy();

                        // verify that inline topics are enabled
                        expect(inlineView.$('.check-discussion-subcategory-inline').prop('disabled')).toBeFalsy();
                        expect(inlineView.$('.check-discussion-category').prop('disabled')).toBeFalsy();
                    });

                    it('has cohorted and non-cohorted topics', function() {
                        createInlineView(this);
                        enableSaveButton();
                        assertCohortedTopics(inlineView, 'inline');
                    });

                    it('enables "Save" button after changing from always inline option', function() {
                        createInlineView(this);
                        enableSaveButton();
                    });

                    it('saves the topic', function() {
                        createInlineView(this);
                        enableSaveButton();

                        // Save the updated settings
                        inlineView.$('.action-save').click();

                        mockPatchRequest(['Inline_Discussion_1']);
                        mockGetRequest();

                        verifySuccess();
                    });

                    it('selects the parent category when all children are selected', function() {
                        createInlineView(this);
                        enableSaveButton();

                        // parent category should be indeterminate.
                        expect(inlineView.$('.check-discussion-category:checked').length).toBe(0);
                        expect(inlineView.$('.check-discussion-category:indeterminate').length).toBe(1);

                        inlineView.$('.check-discussion-subcategory-inline').prop('checked', 'checked').change();
                        // parent should be checked as we checked all children
                        expect(inlineView.$('.check-discussion-category:checked').length).toBe(1);
                    });

                    it('selects/deselects all children when a parent category is selected/deselected', function() {
                        createInlineView(this);
                        enableSaveButton();

                        expect(inlineView.$('.check-discussion-category:checked').length).toBe(0);

                        inlineView.$('.check-discussion-category').prop('checked', 'checked').change();

                        expect(inlineView.$('.check-discussion-category:checked').length).toBe(1);
                        expect(inlineView.$('.check-discussion-subcategory-inline:checked').length).toBe(2);

                        // un-check the parent, all children should be unchecd.
                        inlineView.$('.check-discussion-category').prop('checked', false).change();
                        expect(inlineView.$('.check-discussion-category:checked').length).toBe(0);
                        expect(inlineView.$('.check-discussion-subcategory-inline:checked').length).toBe(0);
                    });

                    it('saves correctly when a subset of topics are selected within a category', function() {
                        createInlineView(this);
                        enableSaveButton();

                        // parent category should be indeterminate.
                        expect(inlineView.$('.check-discussion-category:checked').length).toBe(0);
                        expect(inlineView.$('.check-discussion-category:indeterminate').length).toBe(1);

                        // Save the updated settings
                        inlineView.$('.action-save').click();

                        mockPatchRequest(['Inline_Discussion_1']);
                        mockGetRequest();

                        verifySuccess();
                        // parent category should be indeterminate.
                        expect(inlineView.$('.check-discussion-category:indeterminate').length).toBe(1);
                    });

                    it('saves correctly when all child topics are selected within a category', function() {
                        createInlineView(this);
                        enableSaveButton();

                        // parent category should be indeterminate.
                        expect(inlineView.$('.check-discussion-category:checked').length).toBe(0);
                        expect(inlineView.$('.check-discussion-category:indeterminate').length).toBe(1);

                        inlineView.$('.check-discussion-subcategory-inline').prop('checked', 'checked').change();
                        // Save the updated settings
                        inlineView.$('.action-save').click();

                        mockPatchRequest(['Inline_Discussion_1', 'Inline_Discussion_2']);
                        mockGetRequest(true);

                        verifySuccess();
                        // parent category should be checked.
                        expect(inlineView.$('.check-discussion-category:checked').length).toBe(1);
                    });

                    it('shows an appropriate message when no inline topics exist', function() {

                        var topicsJson, discussionTopicsSettingsModel;

                        topicsJson = {
                            course_wide_discussions: {
                                children: ['Topic_C_1'],
                                entries: {
                                    Topic_C_1: {
                                       sort_key: null,
                                       is_cohorted: true,
                                       id: 'Topic_C_1'
                                    }
                                }
                            },
                            inline_discussions: {
                                subcategories: {},
                                children: []
                            }
                        };
                        discussionTopicsSettingsModel = new DiscussionTopicsSettingsModel(topicsJson);

                        createInlineView(this, discussionTopicsSettingsModel);

                        var expectedTitle = "No content-specific discussion topics exist.";
                        expect(inlineView.$('.no-topics').text().trim()).toBe(expectedTitle);
                    });

                    it('shows an appropriate message when subsequent "GET" returns HTTP500', function() {
                        createInlineView(this);
                        enableSaveButton();

                        // Save the updated settings
                        inlineView.$('.action-save').click();

                        mockPatchRequest(['Inline_Discussion_1']);

                        // fake request for discussion/topics with GET method.
                        AjaxHelpers.expectJsonRequest(
                            requests, 'GET', '/mock_service/cohorts/discussion/topics'
                        );
                        AjaxHelpers.respondWithError(requests, 500);

                        var expectedTitle = "We've encountered an error. Refresh your browser and then try again.";
                        expect(inlineView.$('.message-title').text().trim()).toBe(expectedTitle);
                    });

                    it('shows an appropriate error message for HTTP500', function () {
                        createInlineView(this);
                        enableSaveButton();

                        $(inlineView.$('.check-discussion-subcategory-inline')[1]).prop('checked', 'checked').change();
                        inlineView.$('.action-save').click();

                        AjaxHelpers.respondWithError(requests, 500);
                        var expectedTitle = "We've encountered an error. Refresh your browser and then try again.";
                        expect(inlineView.$('.message-title').text().trim()).toBe(expectedTitle);
                    });

                });

            });
        });
    });
