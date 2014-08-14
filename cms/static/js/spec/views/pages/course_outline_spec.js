define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/view_helpers", "js/views/utils/view_utils",
        "js/views/pages/course_outline", "js/models/xblock_outline_info", "js/utils/date_utils", "js/spec_helpers/edit_helpers"],
    function ($, create_sinon, view_helpers, ViewUtils, CourseOutlinePage, XBlockOutlineInfo, DateUtils, edit_helpers) {

        describe("CourseOutlinePage", function() {
            var createCourseOutlinePage, displayNameInput, model, outlinePage, requests,
                getItemsOfType, getItemHeaders, verifyItemsExpanded, expandItemsAndVerifyState, collapseItemsAndVerifyState,
                createMockCourseJSON, createMockSectionJSON, createMockSubsectionJSON, verifyTypePublishable,
                mockCourseJSON, mockEmptyCourseJSON, mockSingleSectionCourseJSON, createMockVerticalJSON,
                mockOutlinePage = readFixtures('mock/mock-course-outline-page.underscore'),
                mockRerunNotification = readFixtures('mock/mock-course-rerun-notification.underscore');

            createMockCourseJSON = function(options, children) {
                return $.extend(true, {}, {
                    id: 'mock-course',
                    display_name: 'Mock Course',
                    category: 'course',
                    studio_url: '/course/slashes:MockCourse',
                    is_container: true,
                    has_changes: false,
                    published: true,
                    edited_on: 'Jul 02, 2014 at 20:56 UTC',
                    edited_by: 'MockUser',
                    has_explicit_staff_lock: false,
                    child_info: {
                        category: 'chapter',
                        display_name: 'Section',
                        children: []
                    }
                }, options, {child_info: {children: children}});
            };

            createMockSectionJSON = function(options, children) {
                return $.extend(true, {}, {
                    id: 'mock-section',
                    display_name: 'Mock Section',
                    category: 'chapter',
                    studio_url: '/course/slashes:MockCourse',
                    is_container: true,
                    has_changes: false,
                    published: true,
                    edited_on: 'Jul 02, 2014 at 20:56 UTC',
                    edited_by: 'MockUser',
                    has_explicit_staff_lock: false,
                    child_info: {
                        category: 'sequential',
                        display_name: 'Subsection',
                        children: []
                    }
                }, options, {child_info: {children: children}});
            };

            createMockSubsectionJSON = function(options, children) {
                return $.extend(true, {}, {
                    id: 'mock-subsection',
                    display_name: 'Mock Subsection',
                    category: 'sequential',
                    studio_url: '/course/slashes:MockCourse',
                    is_container: true,
                    has_changes: false,
                    published: true,
                    edited_on: 'Jul 02, 2014 at 20:56 UTC',
                    edited_by: 'MockUser',
                    course_graders: '["Lab", "Howework"]',
                    has_explicit_staff_lock: false,
                    child_info: {
                        category: 'vertical',
                        display_name: 'Unit',
                        children: []
                    }
                }, options, {child_info: {children: children}});
            };

            createMockVerticalJSON = function(options) {
                return $.extend(true, {}, {
                    id: 'mock-unit',
                    display_name: 'Mock Unit',
                    category: 'vertical',
                    studio_url: '/container/mock-unit',
                    is_container: true,
                    has_changes: false,
                    published: true,
                    visibility_state: 'unscheduled',
                    edited_on: 'Jul 02, 2014 at 20:56 UTC',
                    edited_by: 'MockUser'
                }, options);
            };

            getItemsOfType = function(type) {
                return outlinePage.$('.outline-' + type);
            };

            getItemHeaders = function(type) {
                return getItemsOfType(type).find('> .' + type + '-header');
            };

            verifyItemsExpanded = function(type, isExpanded) {
                var element = getItemsOfType(type);
                if (isExpanded) {
                    expect(element).not.toHaveClass('is-collapsed');
                } else {
                    expect(element).toHaveClass('is-collapsed');
                }
            };

            expandItemsAndVerifyState = function(type) {
                getItemHeaders(type).find('.ui-toggle-expansion').click();
                verifyItemsExpanded(type, true);
            };

            collapseItemsAndVerifyState = function(type) {
                getItemHeaders(type).find('.ui-toggle-expansion').click();
                verifyItemsExpanded(type, false);
            };

            createCourseOutlinePage = function(test, courseJSON, createOnly) {
                requests = create_sinon.requests(test);
                model = new XBlockOutlineInfo(courseJSON, { parse: true });
                outlinePage = new CourseOutlinePage({
                    model: model,
                    el: $('#content')
                });
                if (!createOnly) {
                    outlinePage.render();
                }
                return outlinePage;
            };

            verifyTypePublishable = function (type, getMockCourseJSON) {
                var createCourseOutlinePageAndShowUnit, verifyPublishButton;

                createCourseOutlinePageAndShowUnit = function (test, courseJSON, createOnly) {
                    outlinePage = createCourseOutlinePage.apply(this, arguments);
                    if (type === 'unit') {
                        expandItemsAndVerifyState('subsection');
                    }
                };

                verifyPublishButton = function (test, courseJSON, createOnly) {
                    createCourseOutlinePageAndShowUnit.apply(this, arguments);
                    expect(getItemHeaders(type).find('.publish-button')).toExist();
                };

                it('can be published', function() {
                    var mockCourseJSON = getMockCourseJSON({
                        has_changes: true
                    });
                    createCourseOutlinePageAndShowUnit(this, mockCourseJSON);
                    getItemHeaders(type).find('.publish-button').click();
                    $(".wrapper-modal-window .action-publish").click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/mock-' + type, {
                        publish : 'make_public'
                    });
                    expect(requests[0].requestHeaders['X-HTTP-Method-Override']).toBe('PATCH');
                    create_sinon.respondWithJson(requests, {});
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-section');
                });

                it('should show publish button if it is not published and not changed', function() {
                    var mockCourseJSON = getMockCourseJSON({
                        has_changes: false,
                        published: false
                    });
                    verifyPublishButton(this, mockCourseJSON);
                });

                it('should show publish button if it is published and changed', function() {
                    var mockCourseJSON = getMockCourseJSON({
                        has_changes: true,
                        published: true
                    });
                    verifyPublishButton(this, mockCourseJSON);
                });

                it('should show publish button if it is not published, but changed', function() {
                    var mockCourseJSON = getMockCourseJSON({
                        has_changes: true,
                        published: false
                    });
                    verifyPublishButton(this, mockCourseJSON);
                });

                it('should hide publish button if it is not changed, but published', function() {
                    var mockCourseJSON = getMockCourseJSON({
                        has_changes: false,
                        published: true
                    });
                    createCourseOutlinePageAndShowUnit(this, mockCourseJSON);
                    expect(getItemHeaders(type).find('.publish-button')).not.toExist();
                });
            };

            beforeEach(function () {
                view_helpers.installMockAnalytics();
                view_helpers.installViewTemplates();
                view_helpers.installTemplates([
                    'course-outline', 'xblock-string-field-editor', 'modal-button',
                    'basic-modal', 'course-outline-modal', 'release-date-editor',
                    'due-date-editor', 'grading-editor', 'publish-editor',
                    'staff-lock-editor'
                ]);
                appendSetFixtures(mockOutlinePage);
                mockCourseJSON = createMockCourseJSON({}, [
                    createMockSectionJSON({}, [
                        createMockSubsectionJSON({}, [
                            createMockVerticalJSON()
                        ])
                    ])
                ]);
                mockEmptyCourseJSON = createMockCourseJSON();
                mockSingleSectionCourseJSON = createMockCourseJSON({}, [
                    createMockSectionJSON()
                ]);
            });

            afterEach(function () {
                view_helpers.removeMockAnalytics();
                edit_helpers.cancelModalIfShowing();
                // Clean up after the $.datepicker
                $("#start_date").datepicker( "destroy" );
                $("#due_date").datepicker( "destroy" );
                $('.ui-datepicker').remove();
            });

            describe('Initial display', function() {
                it('can render itself', function() {
                    createCourseOutlinePage(this, mockCourseJSON);
                    expect(outlinePage.$('.list-sections')).toExist();
                    expect(outlinePage.$('.list-subsections')).toExist();
                    expect(outlinePage.$('.list-units')).toExist();
                });

                it('shows a loading indicator', function() {
                    createCourseOutlinePage(this, mockCourseJSON, true);
                    expect(outlinePage.$('.ui-loading')).not.toHaveClass('is-hidden');
                    outlinePage.render();
                    expect(outlinePage.$('.ui-loading')).toHaveClass('is-hidden');
                });

                it('shows subsections initially collapsed', function() {
                    createCourseOutlinePage(this, mockCourseJSON);
                    verifyItemsExpanded('subsection', false);
                    expect(getItemsOfType('unit')).not.toExist();
                });
            });

            describe("Rerun notification", function () {
                it("can be dismissed", function () {
                    appendSetFixtures(mockRerunNotification);
                    createCourseOutlinePage(this, mockEmptyCourseJSON);
                    expect($('.wrapper-alert-announcement')).not.toHaveClass('is-hidden');
                    $('.dismiss-button').click();
                    create_sinon.expectJsonRequest(requests, 'DELETE', 'dummy_dismiss_url');
                    create_sinon.respondToDelete(requests);
                    expect($('.wrapper-alert-announcement')).toHaveClass('is-hidden');
                });
            });

            describe("Button bar", function() {
                it('can add a section', function() {
                    createCourseOutlinePage(this, mockEmptyCourseJSON);
                    outlinePage.$('.nav-actions .button-new').click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/', {
                        'category': 'chapter',
                        'display_name': 'Section',
                        'parent_locator': 'mock-course'
                    });
                    create_sinon.respondWithJson(requests, {
                        "locator": 'mock-section',
                        "courseKey": 'slashes:MockCourse'
                    });
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-course');
                    create_sinon.respondWithJson(requests, mockSingleSectionCourseJSON);
                    expect(outlinePage.$('.no-content')).not.toExist();
                    expect(outlinePage.$('.list-sections li.outline-section').data('locator')).toEqual('mock-section');
                });

                it('can add a second section', function() {
                    var sectionElements;
                    createCourseOutlinePage(this, mockSingleSectionCourseJSON);
                    outlinePage.$('.nav-actions .button-new').click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/', {
                        'category': 'chapter',
                        'display_name': 'Section',
                        'parent_locator': 'mock-course'
                    });
                    create_sinon.respondWithJson(requests, {
                        "locator": 'mock-section-2',
                        "courseKey": 'slashes:MockCourse'
                    });
                    // Expect the UI to just fetch the new section and repaint it
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-section-2');
                    create_sinon.respondWithJson(requests,
                        createMockSectionJSON({id: 'mock-section-2', display_name: 'Mock Section 2'}));
                    sectionElements = getItemsOfType('section');
                    expect(sectionElements.length).toBe(2);
                    expect($(sectionElements[0]).data('locator')).toEqual('mock-section');
                    expect($(sectionElements[1]).data('locator')).toEqual('mock-section-2');
                });

                it('can expand and collapse all sections', function() {
                    createCourseOutlinePage(this, mockCourseJSON, false);
                    verifyItemsExpanded('section', true);
                    outlinePage.$('.nav-actions .button-toggle-expand-collapse .collapse-all').click();
                    verifyItemsExpanded('section', false);
                    outlinePage.$('.nav-actions .button-toggle-expand-collapse .expand-all').click();
                    verifyItemsExpanded('section', true);
                });
            });

            describe("Empty course", function() {
                it('shows an empty course message initially', function() {
                    createCourseOutlinePage(this, mockEmptyCourseJSON);
                    expect(outlinePage.$('.no-content')).not.toHaveClass('is-hidden');
                    expect(outlinePage.$('.no-content .button-new')).toExist();
                });

                it('can add a section', function() {
                    createCourseOutlinePage(this, mockEmptyCourseJSON);
                    $('.no-content .button-new').click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/', {
                        'category': 'chapter',
                        'display_name': 'Section',
                        'parent_locator': 'mock-course'
                    });
                    create_sinon.respondWithJson(requests, {
                        "locator": "mock-section",
                        "courseKey": "slashes:MockCourse"
                    });
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-course');
                    create_sinon.respondWithJson(requests, mockSingleSectionCourseJSON);
                    expect(outlinePage.$('.no-content')).not.toExist();
                    expect(outlinePage.$('.list-sections li.outline-section').data('locator')).toEqual('mock-section');
                });

                it('remains empty if an add fails', function() {
                    var requestCount;
                    createCourseOutlinePage(this, mockEmptyCourseJSON);
                    $('.no-content .button-new').click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/', {
                        'category': 'chapter',
                        'display_name': 'Section',
                        'parent_locator': 'mock-course'
                    });
                    requestCount = requests.length;
                    create_sinon.respondWithError(requests);
                    expect(requests.length).toBe(requestCount); // No additional requests should be made
                    expect(outlinePage.$('.no-content')).not.toHaveClass('is-hidden');
                    expect(outlinePage.$('.no-content .button-new')).toExist();
                });
            });

            describe("Section", function() {
                var getDisplayNameWrapper;

                getDisplayNameWrapper = function() {
                    return getItemHeaders('section').find('.wrapper-xblock-field');
                };

                it('can be deleted', function() {
                    var promptSpy = view_helpers.createPromptSpy(), requestCount;
                    createCourseOutlinePage(this, createMockCourseJSON({}, [
                        createMockSectionJSON(),
                        createMockSectionJSON({id: 'mock-section-2', display_name: 'Mock Section 2'})
                    ]));
                    getItemHeaders('section').find('.delete-button').first().click();
                    view_helpers.confirmPrompt(promptSpy);
                    requestCount = requests.length;
                    create_sinon.expectJsonRequest(requests, 'DELETE', '/xblock/mock-section');
                    create_sinon.respondWithJson(requests, {});
                    expect(requests.length).toBe(requestCount); // No fetch should be performed
                    expect(outlinePage.$('[data-locator="mock-section"]')).not.toExist();
                    expect(outlinePage.$('[data-locator="mock-section-2"]')).toExist();
                });

                it('can be deleted if it is the only section', function() {
                    var promptSpy = view_helpers.createPromptSpy();
                    createCourseOutlinePage(this, mockSingleSectionCourseJSON);
                    getItemHeaders('section').find('.delete-button').click();
                    view_helpers.confirmPrompt(promptSpy);
                    create_sinon.expectJsonRequest(requests, 'DELETE', '/xblock/mock-section');
                    create_sinon.respondWithJson(requests, {});
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-course');
                    create_sinon.respondWithJson(requests, mockEmptyCourseJSON);
                    expect(outlinePage.$('.no-content')).not.toHaveClass('is-hidden');
                    expect(outlinePage.$('.no-content .button-new')).toExist();
                });

                it('remains visible if its deletion fails', function() {
                    var promptSpy = view_helpers.createPromptSpy(),
                        requestCount;
                    createCourseOutlinePage(this, mockSingleSectionCourseJSON);
                    getItemHeaders('section').find('.delete-button').click();
                    view_helpers.confirmPrompt(promptSpy);
                    create_sinon.expectJsonRequest(requests, 'DELETE', '/xblock/mock-section');
                    requestCount = requests.length;
                    create_sinon.respondWithError(requests);
                    expect(requests.length).toBe(requestCount); // No additional requests should be made
                    expect(outlinePage.$('.list-sections li.outline-section').data('locator')).toEqual('mock-section');
                });

                it('can add a subsection', function() {
                    createCourseOutlinePage(this, mockCourseJSON);
                    getItemsOfType('section').find('> .outline-content > .add-subsection .button-new').click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/', {
                        'category': 'sequential',
                        'display_name': 'Subsection',
                        'parent_locator': 'mock-section'
                    });
                    create_sinon.respondWithJson(requests, {
                        "locator": "new-mock-subsection",
                        "courseKey": "slashes:MockCourse"
                    });
                    // Note: verification of the server response and the UI's handling of it
                    // is handled in the acceptance tests.
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-section');

                });

                it('can be renamed inline', function() {
                    var updatedDisplayName = 'Updated Section Name',
                        displayNameWrapper,
                        sectionModel;
                    createCourseOutlinePage(this, mockCourseJSON);
                    displayNameWrapper = getDisplayNameWrapper();
                    displayNameInput = view_helpers.inlineEdit(displayNameWrapper, updatedDisplayName);
                    displayNameInput.change();
                    // This is the response for the change operation.
                    create_sinon.respondWithJson(requests, { });
                    // This is the response for the subsequent fetch operation.
                    create_sinon.respondWithJson(requests, {"display_name":  updatedDisplayName});
                    view_helpers.verifyInlineEditChange(displayNameWrapper, updatedDisplayName);
                    sectionModel = outlinePage.model.get('child_info').children[0];
                    expect(sectionModel.get('display_name')).toBe(updatedDisplayName);
                });

                it('can be expanded and collapsed', function() {
                    createCourseOutlinePage(this, mockCourseJSON);
                    collapseItemsAndVerifyState('section');
                    expandItemsAndVerifyState('section');
                    collapseItemsAndVerifyState('section');
                });

                it('can be edited', function() {
                    createCourseOutlinePage(this, mockCourseJSON, false);
                    outlinePage.$('.section-header-actions .configure-button').click();
                    $("#start_date").val("1/2/2015");
                    // Section release date can't be cleared.
                    expect($(".wrapper-modal-window .action-clear")).not.toExist();

                    // Section does not contain due_date or grading type selector
                    expect($("due_date")).not.toExist();
                    expect($("grading_format")).not.toExist();

                    // Staff lock controls are always visible
                    expect($("#staff_lock")).toExist();
                    $(".wrapper-modal-window .action-save").click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/mock-section', {
                        "metadata":{
                            "start":"2015-01-02T00:00:00.000Z"
                        }
                    });
                    expect(requests[0].requestHeaders['X-HTTP-Method-Override']).toBe('PATCH');

                    // This is the response for the change operation.
                    create_sinon.respondWithJson(requests, {});
                    var mockResponseSectionJSON = createMockSectionJSON({
                            release_date: 'Jan 02, 2015 at 00:00 UTC'
                        }, [
                            createMockSubsectionJSON({}, [
                                createMockVerticalJSON({
                                    has_changes: true,
                                    published: false
                                })
                            ])
                        ]);
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-section')
                    expect(requests.length).toBe(2);
                    // This is the response for the subsequent fetch operation for the section.
                    create_sinon.respondWithJson(requests, mockResponseSectionJSON);

                    expect($(".outline-section .status-release-value")).toContainText("Jan 02, 2015 at 00:00 UTC");
                });

                verifyTypePublishable('section', function (options) {
                    return createMockCourseJSON({}, [
                        createMockSectionJSON(options, [
                            createMockSubsectionJSON({}, [
                                createMockVerticalJSON()
                            ])
                        ])
                    ]);
                });

                it('can display a publish modal with a list of unpublished subsections and units', function () {
                    var mockCourseJSON = createMockCourseJSON({}, [
                            createMockSectionJSON({has_changes: true}, [
                                createMockSubsectionJSON({has_changes: true}, [
                                    createMockVerticalJSON(),
                                    createMockVerticalJSON({has_changes: true, display_name: 'Unit 100'}),
                                    createMockVerticalJSON({published: false, display_name: 'Unit 50'})
                                ]),
                                createMockSubsectionJSON({has_changes: true}, [
                                    createMockVerticalJSON({has_changes: true, display_name: 'Unit 1'})
                                ]),
                                createMockSubsectionJSON({}, [createMockVerticalJSON])
                            ]),
                            createMockSectionJSON({has_changes: true}, [
                                createMockSubsectionJSON({has_changes: true}, [
                                    createMockVerticalJSON({has_changes: true}),
                                ])
                            ])
                        ]), modalWindow;

                    createCourseOutlinePage(this, mockCourseJSON, false);
                    getItemHeaders('section').first().find('.publish-button').click();
                    modalWindow = $('.wrapper-modal-window');
                    expect(modalWindow.find('.outline-unit').length).toBe(3);
                    expect(_.compact(_.map(modalWindow.find('.outline-unit').text().split("\n"), $.trim))).toEqual(
                        ['Unit 100', 'Unit 50', 'Unit 1']
                    )
                    expect(modalWindow.find('.outline-subsection').length).toBe(2);
                });
            });

            describe("Subsection", function() {
                var getDisplayNameWrapper, setEditModalValues, mockServerValuesJson;

                getDisplayNameWrapper = function() {
                    return getItemHeaders('subsection').find('.wrapper-xblock-field');
                };

                setEditModalValues = function (start_date, due_date, grading_type, is_locked) {
                    $("#start_date").val(start_date);
                    $("#due_date").val(due_date);
                    $("#grading_type").val(grading_type);
                    $("#staff_lock").prop('checked', is_locked);
                };

                // Contains hard-coded dates because dates are presented in different formats.
                var mockServerValuesJson = createMockSectionJSON({
                        release_date: 'Jan 01, 2970 at 05:00 UTC'
                    }, [
                        createMockSubsectionJSON({
                            graded: true,
                            due_date: 'Jul 10, 2014 at 00:00 UTC',
                            release_date: 'Jul 09, 2014 at 00:00 UTC',
                            start: "2014-07-09T00:00:00Z",
                            format: "Lab",
                            due: "2014-07-10T00:00:00Z",
                            has_explicit_staff_lock: true,
                            staff_only_message: true
                        }, [
                            createMockVerticalJSON({
                                has_changes: true,
                                published: false
                            })
                        ])
                    ]);

                it('can be deleted', function() {
                    var promptSpy = view_helpers.createPromptSpy();
                    createCourseOutlinePage(this, mockCourseJSON);
                    getItemHeaders('subsection').find('.delete-button').click();
                    view_helpers.confirmPrompt(promptSpy);
                    create_sinon.expectJsonRequest(requests, 'DELETE', '/xblock/mock-subsection');
                    create_sinon.respondWithJson(requests, {});
                    // Note: verification of the server response and the UI's handling of it
                    // is handled in the acceptance tests.
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-section');
                });

                it('can add a unit', function() {
                    var redirectSpy;
                    createCourseOutlinePage(this, mockCourseJSON);
                    redirectSpy = spyOn(ViewUtils, 'redirect');
                    getItemsOfType('subsection').find('> .outline-content > .add-unit .button-new').click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/', {
                        'category': 'vertical',
                        'display_name': 'Unit',
                        'parent_locator': 'mock-subsection'
                    });
                    create_sinon.respondWithJson(requests, {
                        "locator": "new-mock-unit",
                        "courseKey": "slashes:MockCourse"
                    });
                    expect(redirectSpy).toHaveBeenCalledWith('/container/new-mock-unit?action=new');
                });

                it('can be renamed inline', function() {
                    var updatedDisplayName = 'Updated Subsection Name',
                        displayNameWrapper,
                        subsectionModel;
                    createCourseOutlinePage(this, mockCourseJSON);
                    displayNameWrapper = getDisplayNameWrapper();
                    displayNameInput = view_helpers.inlineEdit(displayNameWrapper, updatedDisplayName);
                    displayNameInput.change();
                    // This is the response for the change operation.
                    create_sinon.respondWithJson(requests, { });
                    // This is the response for the subsequent fetch operation for the section.
                    create_sinon.respondWithJson(requests,
                        createMockSectionJSON({}, [
                            createMockSubsectionJSON({
                                display_name: updatedDisplayName
                            })
                        ])
                    );
                    // Find the display name again in the refreshed DOM and verify it
                    displayNameWrapper = getItemHeaders('subsection').find('.wrapper-xblock-field');
                    view_helpers.verifyInlineEditChange(displayNameWrapper, updatedDisplayName);
                    subsectionModel = outlinePage.model.get('child_info').children[0].get('child_info').children[0];
                    expect(subsectionModel.get('display_name')).toBe(updatedDisplayName);
                });

                it('can be expanded and collapsed', function() {
                    createCourseOutlinePage(this, mockCourseJSON);
                    verifyItemsExpanded('subsection', false);
                    expandItemsAndVerifyState('subsection');
                    collapseItemsAndVerifyState('subsection');
                    expandItemsAndVerifyState('subsection');
                });

                it('can be edited', function() {
                    createCourseOutlinePage(this, mockCourseJSON, false);
                    outlinePage.$('.outline-subsection .configure-button').click();
                    setEditModalValues("7/9/2014", "7/10/2014", "Lab", true);
                    $(".wrapper-modal-window .action-save").click();
                    create_sinon.expectJsonRequest(requests, 'POST', '/xblock/mock-subsection', {
                        "graderType":"Lab",
                        "publish": "republish",
                        "metadata":{
                            "visible_to_staff_only": true,
                            "start":"2014-07-09T00:00:00.000Z",
                            "due":"2014-07-10T00:00:00.000Z"
                        }
                    });
                    expect(requests[0].requestHeaders['X-HTTP-Method-Override']).toBe('PATCH');

                    // This is the response for the change operation.
                    create_sinon.respondWithJson(requests, {});
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-section')
                    expect(requests.length).toBe(2);
                    // This is the response for the subsequent fetch operation for the section.
                    create_sinon.respondWithJson(requests, mockServerValuesJson);

                    expect($(".outline-subsection .status-release-value")).toContainText("Jul 09, 2014 at 00:00 UTC");
                    expect($(".outline-subsection .status-grading-date")).toContainText("Due: Jul 10, 2014 at 00:00 UTC");
                    expect($(".outline-subsection .status-grading-value")).toContainText("Lab");
                    expect($(".outline-subsection .status-message-copy")).toContainText("Contains staff only content");

                    expect($(".outline-item .outline-subsection .status-grading-value")).toContainText("Lab");
                    outlinePage.$('.outline-item .outline-subsection .configure-button').click();
                    expect($("#start_date").val()).toBe('7/9/2014');
                    expect($("#due_date").val()).toBe('7/10/2014');
                    expect($("#grading_type").val()).toBe('Lab');
                    expect($("#staff_lock").is(":checked")).toBe(true);
                });

                it('release date, due date, grading type, and staff lock can be cleared.', function() {
                    createCourseOutlinePage(this, mockCourseJSON, false);
                    outlinePage.$('.outline-item .outline-subsection .configure-button').click();
                    setEditModalValues("7/9/2014", "7/10/2014", "Lab", true);
                    $(".wrapper-modal-window .action-save").click();

                    // This is the response for the change operation.
                    create_sinon.respondWithJson(requests, {});
                    // This is the response for the subsequent fetch operation.
                    create_sinon.respondWithJson(requests, mockServerValuesJson);

                    expect($(".outline-subsection .status-release-value")).toContainText("Jul 09, 2014 at 00:00 UTC");
                    expect($(".outline-subsection .status-grading-date")).toContainText("Due: Jul 10, 2014 at 00:00 UTC");
                    expect($(".outline-subsection .status-grading-value")).toContainText("Lab");
                    expect($(".outline-subsection .status-message-copy")).toContainText("Contains staff only content");

                    outlinePage.$('.outline-subsection .configure-button').click();
                    expect($("#start_date").val()).toBe('7/9/2014');
                    expect($("#due_date").val()).toBe('7/10/2014');
                    expect($("#grading_type").val()).toBe('Lab');
                    expect($("#staff_lock").is(":checked")).toBe(true);

                    $(".wrapper-modal-window .scheduled-date-input .action-clear").click();
                    $(".wrapper-modal-window .due-date-input .action-clear").click();
                    expect($("#start_date").val()).toBe('');
                    expect($("#due_date").val()).toBe('');

                    $("#grading_type").val('notgraded');
                    $("#staff_lock").prop('checked', false);

                    $(".wrapper-modal-window .action-save").click();

                    // This is the response for the change operation.
                    create_sinon.respondWithJson(requests, {});
                    // This is the response for the subsequent fetch operation.
                    create_sinon.respondWithJson(requests,
                        createMockSectionJSON({}, [createMockSubsectionJSON()])
                    );
                    expect($(".outline-subsection .status-release-value")).not.toContainText("Jul 09, 2014 at 00:00 UTC");
                    expect($(".outline-subsection .status-grading-date")).not.toExist();
                    expect($(".outline-subsection .status-grading-value")).not.toExist();
                    expect($(".outline-subsection .status-message-copy")).not.toContainText("Contains staff only content");
                });

                verifyTypePublishable('subsection', function (options) {
                    return createMockCourseJSON({}, [
                        createMockSectionJSON({}, [
                            createMockSubsectionJSON(options, [
                                createMockVerticalJSON()
                            ])
                        ])
                    ]);
                });

                it('can display a publish modal with a list of unpublished units', function () {
                    var mockCourseJSON = createMockCourseJSON({}, [
                            createMockSectionJSON({has_changes: true}, [
                                createMockSubsectionJSON({has_changes: true}, [
                                    createMockVerticalJSON(),
                                    createMockVerticalJSON({has_changes: true, display_name: "Unit 100"}),
                                    createMockVerticalJSON({published: false, display_name: "Unit 50"})
                                ]),
                                createMockSubsectionJSON({has_changes: true}, [
                                    createMockVerticalJSON({has_changes: true})
                                ]),
                                createMockSubsectionJSON({}, [createMockVerticalJSON])
                            ])
                        ]), modalWindow;

                    createCourseOutlinePage(this, mockCourseJSON, false);
                    getItemHeaders('subsection').first().find('.publish-button').click();
                    modalWindow = $('.wrapper-modal-window');
                    expect(modalWindow.find('.outline-unit').length).toBe(2);
                    expect(_.compact(_.map(modalWindow.find('.outline-unit').text().split("\n"), $.trim))).toEqual(
                        ['Unit 100', 'Unit 50']
                    )
                    expect(modalWindow.find('.outline-subsection')).not.toExist();
                });
            });

            // Note: most tests for units can be found in Bok Choy
            describe("Unit", function() {
                it('can be deleted', function() {
                    var promptSpy = view_helpers.createPromptSpy();
                    createCourseOutlinePage(this, mockCourseJSON);
                    expandItemsAndVerifyState('subsection');
                    getItemHeaders('unit').find('.delete-button').click();
                    view_helpers.confirmPrompt(promptSpy);
                    create_sinon.expectJsonRequest(requests, 'DELETE', '/xblock/mock-unit');
                    create_sinon.respondWithJson(requests, {});
                    // Note: verification of the server response and the UI's handling of it
                    // is handled in the acceptance tests.
                    create_sinon.expectJsonRequest(requests, 'GET', '/xblock/outline/mock-section');
                });

                it('has a link to the unit page', function() {
                    var unitAnchor;
                    createCourseOutlinePage(this, mockCourseJSON);
                    expandItemsAndVerifyState('subsection');
                    unitAnchor = getItemsOfType('unit').find('.unit-title a');
                    expect(unitAnchor.attr('href')).toBe('/container/mock-unit');
                });

                verifyTypePublishable('unit', function (options) {
                    return createMockCourseJSON({}, [
                        createMockSectionJSON({}, [
                            createMockSubsectionJSON({}, [
                                createMockVerticalJSON(options)
                            ])
                        ])
                    ]);
                });
            });

            describe("Date and Time picker", function() {
                // Two datetime formats can came from server: '%Y-%m-%dT%H:%M:%SZ' and %Y-%m-%dT%H:%M:%S+TZ:TZ'
                it('can parse dates in both formats that can come from server', function() {
                    createCourseOutlinePage(this, mockCourseJSON, false);
                    outlinePage.$('.outline-subsection .configure-button').click();
                    expect($("#start_date").val()).toBe('');
                    expect($("#start_time").val()).toBe('');
                    DateUtils.setDate($("#start_date"), ("#start_time"), "2015-08-10T05:10:00Z");
                    expect($("#start_date").val()).toBe('8/10/2015');
                    expect($("#start_time").val()).toBe('05:10');
                    DateUtils.setDate($("#start_date"), ("#start_time"), "2014-07-09T00:00:00+00:00");
                    expect($("#start_date").val()).toBe('7/9/2014');
                    expect($("#start_time").val()).toBe('00:00');
                });
            });
        });
    });
