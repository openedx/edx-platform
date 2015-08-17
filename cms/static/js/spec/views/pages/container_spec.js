define(["jquery", "underscore", "underscore.string", "common/js/spec_helpers/ajax_helpers",
        "common/js/spec_helpers/template_helpers", "js/spec_helpers/edit_helpers",
        "js/views/pages/container", "js/views/pages/paged_container", "js/models/xblock_info", "jquery.simulate"],
    function ($, _, str, AjaxHelpers, TemplateHelpers, EditHelpers, ContainerPage, PagedContainerPage, XBlockInfo) {

        function parameterized_suite(label, global_page_options, fixtures) {
            describe(label + " ContainerPage", function () {
                var lastRequest, getContainerPage, renderContainerPage, expectComponents, respondWithHtml,
                    model, containerPage, requests, initialDisplayName,
                    mockContainerPage = readFixtures('mock/mock-container-page.underscore'),
                    mockContainerXBlockHtml = readFixtures(fixtures.initial),
                    mockXBlockHtml = readFixtures(fixtures.add_response),
                    mockBadContainerXBlockHtml = readFixtures('mock/mock-bad-javascript-container-xblock.underscore'),
                    mockBadXBlockContainerXBlockHtml = readFixtures('mock/mock-bad-xblock-container-xblock.underscore'),
                    mockUpdatedContainerXBlockHtml = readFixtures('mock/mock-updated-container-xblock.underscore'),
                    mockXBlockEditorHtml = readFixtures('mock/mock-xblock-editor.underscore'),
                    mockXBlockVisibilityEditorHtml = readFixtures('mock/mock-xblock-visibility-editor.underscore'),
                    PageClass = fixtures.page,
                    pagedSpecificTests = fixtures.paged_specific_tests,
                    hasVisibilityEditor = fixtures.has_visibility_editor;

                beforeEach(function () {
                    var newDisplayName = 'New Display Name';

                    EditHelpers.installEditTemplates();
                    TemplateHelpers.installTemplate('xblock-string-field-editor');
                    TemplateHelpers.installTemplate('container-message');
                    appendSetFixtures(mockContainerPage);

                    EditHelpers.installMockXBlock({
                        data: "<p>Some HTML</p>",
                        metadata: {
                            display_name: newDisplayName
                        }
                    });

                    initialDisplayName = 'Test Container';

                    model = new XBlockInfo({
                        id: 'locator-container',
                        display_name: initialDisplayName,
                        category: 'vertical'
                    });
                });

                afterEach(function () {
                    EditHelpers.uninstallMockXBlock();
                });

                lastRequest = function () {
                    return requests[requests.length - 1];
                };

                respondWithHtml = function (html) {
                    var requestIndex = requests.length - 1;
                    AjaxHelpers.respondWithJson(
                        requests,
                        { html: html, "resources": [] },
                        requestIndex
                    );
                };

                getContainerPage = function (options) {
                    var default_options = {
                        model: model,
                        templates: EditHelpers.mockComponentTemplates,
                        el: $('#content')
                    };
                    return new PageClass(_.extend(options || {}, global_page_options, default_options));
                };

                renderContainerPage = function (test, html, options) {
                    requests = AjaxHelpers.requests(test);
                    containerPage = getContainerPage(options);
                    containerPage.render();
                    respondWithHtml(html);
                };

                expectComponents = function (container, locators) {
                    // verify expected components (in expected order) by their locators
                    var components = $(container).find('.studio-xblock-wrapper');
                    expect(components.length).toBe(locators.length);
                    _.each(locators, function (locator, locator_index) {
                        expect($(components[locator_index]).data('locator')).toBe(locator);
                    });
                };

                describe("Initial display", function () {
                    it('can render itself', function () {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        expect(containerPage.$('.xblock-header').length).toBe(9);
                        expect(containerPage.$('.wrapper-xblock .level-nesting')).not.toHaveClass('is-hidden');
                    });

                    it('shows a loading indicator', function () {
                        requests = AjaxHelpers.requests(this);
                        containerPage = getContainerPage();
                        containerPage.render();
                        expect(containerPage.$('.ui-loading')).not.toHaveClass('is-hidden');
                        respondWithHtml(mockContainerXBlockHtml);
                        expect(containerPage.$('.ui-loading')).toHaveClass('is-hidden');
                    });

                    it('can show an xblock with broken JavaScript', function () {
                        renderContainerPage(this, mockBadContainerXBlockHtml);
                        expect(containerPage.$('.wrapper-xblock .level-nesting')).not.toHaveClass('is-hidden');
                        expect(containerPage.$('.ui-loading')).toHaveClass('is-hidden');
                    });

                    it('can show an xblock with an invalid XBlock', function () {
                        renderContainerPage(this, mockBadXBlockContainerXBlockHtml);
                        expect(containerPage.$('.wrapper-xblock .level-nesting')).not.toHaveClass('is-hidden');
                        expect(containerPage.$('.ui-loading')).toHaveClass('is-hidden');
                    });

                    it('inline edits the display name when performing a new action', function () {
                        renderContainerPage(this, mockContainerXBlockHtml, {
                            action: 'new'
                        });
                        expect(containerPage.$('.xblock-header').length).toBe(9);
                        expect(containerPage.$('.wrapper-xblock .level-nesting')).not.toHaveClass('is-hidden');
                        expect(containerPage.$('.xblock-field-input')).not.toHaveClass('is-hidden');
                    });
                });

                describe("Editing the container", function () {
                    var updatedDisplayName = 'Updated Test Container',
                        getDisplayNameWrapper;

                    afterEach(function () {
                        EditHelpers.cancelModalIfShowing();
                    });

                    getDisplayNameWrapper = function () {
                        return containerPage.$('.wrapper-xblock-field');
                    };

                    it('can edit itself', function () {
                        var editButtons, displayNameElement;
                        renderContainerPage(this, mockContainerXBlockHtml);
                        displayNameElement = containerPage.$('.page-header-title');

                        // Click the root edit button
                        editButtons = containerPage.$('.nav-actions .edit-button');
                        editButtons.first().click();

                        // Expect a request to be made to show the studio view for the container
                        expect(str.startsWith(lastRequest().url, '/xblock/locator-container/studio_view')).toBeTruthy();
                        AjaxHelpers.respondWithJson(requests, {
                            html: mockContainerXBlockHtml,
                            resources: []
                        });
                        expect(EditHelpers.isShowingModal()).toBeTruthy();

                        // Expect the correct title to be shown
                        expect(EditHelpers.getModalTitle()).toBe('Editing: Test Container');

                        // Press the save button and respond with a success message to the save
                        EditHelpers.pressModalButton('.action-save');
                        AjaxHelpers.respondWithJson(requests, { });
                        expect(EditHelpers.isShowingModal()).toBeFalsy();

                        // Expect the last request be to refresh the container page
                        expect(str.startsWith(lastRequest().url,
                            '/xblock/locator-container/container_preview')).toBeTruthy();
                        AjaxHelpers.respondWithJson(requests, {
                            html: mockUpdatedContainerXBlockHtml,
                            resources: []
                        });

                        // Respond to the subsequent xblock info fetch request.
                        AjaxHelpers.respondWithJson(requests, {"display_name": updatedDisplayName});

                        // Expect the title to have been updated
                        expect(displayNameElement.text().trim()).toBe(updatedDisplayName);
                    });

                    it('can inline edit the display name', function () {
                        var displayNameInput, displayNameWrapper;
                        renderContainerPage(this, mockContainerXBlockHtml);
                        displayNameWrapper = getDisplayNameWrapper();
                        displayNameInput = EditHelpers.inlineEdit(displayNameWrapper, updatedDisplayName);
                        displayNameInput.change();
                        // This is the response for the change operation.
                        AjaxHelpers.respondWithJson(requests, { });
                        // This is the response for the subsequent fetch operation.
                        AjaxHelpers.respondWithJson(requests, {"display_name": updatedDisplayName});
                        EditHelpers.verifyInlineEditChange(displayNameWrapper, updatedDisplayName);
                        expect(containerPage.model.get('display_name')).toBe(updatedDisplayName);
                    });
                });

                describe("Editing an xblock", function () {
                    afterEach(function () {
                        EditHelpers.cancelModalIfShowing();
                    });

                    it('can show an edit modal for a child xblock', function () {
                        var editButtons;
                        renderContainerPage(this, mockContainerXBlockHtml);
                        editButtons = containerPage.$('.wrapper-xblock .edit-button');
                        // The container should have rendered six mock xblocks
                        expect(editButtons.length).toBe(6);
                        editButtons[0].click();
                        // Make sure that the correct xblock is requested to be edited
                        expect(str.startsWith(lastRequest().url, '/xblock/locator-component-A1/studio_view')).toBeTruthy();
                        AjaxHelpers.respondWithJson(requests, {
                            html: mockXBlockEditorHtml,
                            resources: []
                        });
                        expect(EditHelpers.isShowingModal()).toBeTruthy();
                    });

                    it('can show an edit modal for a child xblock with broken JavaScript', function () {
                        var editButtons;
                        renderContainerPage(this, mockBadContainerXBlockHtml);
                        editButtons = containerPage.$('.wrapper-xblock .edit-button');
                        editButtons[0].click();
                        AjaxHelpers.respondWithJson(requests, {
                            html: mockXBlockEditorHtml,
                            resources: []
                        });
                        expect(EditHelpers.isShowingModal()).toBeTruthy();
                    });

                    it('can show a visibility modal for a child xblock if supported for the page', function() {
                        var visibilityButtons;
                        renderContainerPage(this, mockContainerXBlockHtml);
                        visibilityButtons = containerPage.$('.wrapper-xblock .visibility-button');
                        if (hasVisibilityEditor) {
                            expect(visibilityButtons.length).toBe(6);
                            visibilityButtons[0].click();
                            expect(str.startsWith(lastRequest().url, '/xblock/locator-component-A1/visibility_view'))
                                .toBeTruthy();
                            AjaxHelpers.respondWithJson(requests, {
                                html: mockXBlockVisibilityEditorHtml,
                                resources: []
                            });
                            expect(EditHelpers.isShowingModal()).toBeTruthy();
                        }
                        else {
                            expect(visibilityButtons.length).toBe(0);
                        }
                    });
                });

                describe("Editing an xmodule", function () {
                    var mockXModuleEditor = readFixtures('mock/mock-xmodule-editor.underscore'),
                        newDisplayName = 'New Display Name';

                    beforeEach(function () {
                        EditHelpers.installMockXModule({
                            data: "<p>Some HTML</p>",
                            metadata: {
                                display_name: newDisplayName
                            }
                        });
                    });

                    afterEach(function () {
                        EditHelpers.uninstallMockXModule();
                        EditHelpers.cancelModalIfShowing();
                    });

                    it('can save changes to settings', function () {
                        var editButtons, modal, mockUpdatedXBlockHtml;
                        mockUpdatedXBlockHtml = readFixtures('mock/mock-updated-xblock.underscore');
                        renderContainerPage(this, mockContainerXBlockHtml);
                        editButtons = containerPage.$('.wrapper-xblock .edit-button');
                        // The container should have rendered six mock xblocks
                        expect(editButtons.length).toBe(6);
                        editButtons[0].click();
                        AjaxHelpers.respondWithJson(requests, {
                            html: mockXModuleEditor,
                            resources: []
                        });

                        modal = $('.edit-xblock-modal');
                        expect(modal.length).toBe(1);
                        // Click on the settings tab
                        modal.find('.settings-button').click();
                        // Change the display name's text
                        modal.find('.setting-input').text("Mock Update");
                        // Press the save button
                        modal.find('.action-save').click();
                        // Respond to the save
                        AjaxHelpers.respondWithJson(requests, {
                            id: model.id
                        });

                        // Respond to the request to refresh
                        respondWithHtml(mockUpdatedXBlockHtml);

                        // Verify that the xblock was updated
                        expect(containerPage.$('.mock-updated-content').text()).toBe('Mock Update');
                    });
                });

                describe("xblock operations", function () {
                    var getGroupElement, paginated, getDeleteOffset,
                        NUM_COMPONENTS_PER_GROUP = 3, GROUP_TO_TEST = "A",
                        allComponentsInGroup = _.map(
                            _.range(NUM_COMPONENTS_PER_GROUP),
                            function (index) {
                                return 'locator-component-' + GROUP_TO_TEST + (index + 1);
                            }
                        );

                    getDeleteOffset = function () {
                        // Paginated containers will make an additional AJAX request.
                        return pagedSpecificTests ? 3 : 2;
                    };

                    getGroupElement = function () {
                        return containerPage.$("[data-locator='locator-group-" + GROUP_TO_TEST + "']");
                    };

                    describe("Deleting an xblock", function () {
                        var clickDelete, deleteComponent, deleteComponentWithSuccess,
                            promptSpy;

                        beforeEach(function () {
                            promptSpy = EditHelpers.createPromptSpy();
                        });


                        clickDelete = function (componentIndex, clickNo) {

                            // find all delete buttons for the given group
                            var deleteButtons = getGroupElement().find(".delete-button");
                            expect(deleteButtons.length).toBe(NUM_COMPONENTS_PER_GROUP);

                            // click the requested delete button
                            deleteButtons[componentIndex].click();

                            // click the 'yes' or 'no' button in the prompt
                            EditHelpers.confirmPrompt(promptSpy, clickNo);
                        };

                        deleteComponent = function (componentIndex, requestOffset) {
                            clickDelete(componentIndex);
                            AjaxHelpers.respondWithJson(requests, {});
                            AjaxHelpers.expectJsonRequest(requests, 'DELETE',
                                    '/xblock/locator-component-' + GROUP_TO_TEST + (componentIndex + 1),
                                null, requests.length - requestOffset);

                            // final request to refresh the xblock info
                            AjaxHelpers.expectJsonRequest(requests, 'GET', '/xblock/locator-container');
                        };

                        deleteComponentWithSuccess = function (componentIndex) {
                            var deleteOffset;

                            deleteOffset = getDeleteOffset();
                            deleteComponent(componentIndex, deleteOffset);

                            // verify the new list of components within the group
                            expectComponents(
                                getGroupElement(),
                                _.without(allComponentsInGroup, allComponentsInGroup[componentIndex])
                            );
                        };

                        it("can delete the first xblock", function () {
                            renderContainerPage(this, mockContainerXBlockHtml);
                            deleteComponentWithSuccess(0);
                        });

                        it("can delete a middle xblock", function () {
                            renderContainerPage(this, mockContainerXBlockHtml);
                            deleteComponentWithSuccess(1);
                        });

                        it("can delete the last xblock", function () {
                            renderContainerPage(this, mockContainerXBlockHtml);
                            deleteComponentWithSuccess(NUM_COMPONENTS_PER_GROUP - 1);
                        });

                        it("can delete an xblock with broken JavaScript", function () {
                            var deleteOffset = getDeleteOffset();
                            renderContainerPage(this, mockBadContainerXBlockHtml);
                            containerPage.$('.delete-button').first().click();
                            EditHelpers.confirmPrompt(promptSpy);
                            AjaxHelpers.respondWithJson(requests, {});

                            // expect the second to last request to be a delete of the xblock
                            AjaxHelpers.expectJsonRequest(requests, 'DELETE', '/xblock/locator-broken-javascript',
                                null, requests.length - deleteOffset);
                            // expect the last request to be a fetch of the xblock info for the parent container
                            AjaxHelpers.expectJsonRequest(requests, 'GET', '/xblock/locator-container');
                        });

                        it('does not delete when clicking No in prompt', function () {
                            var numRequests;

                            renderContainerPage(this, mockContainerXBlockHtml);
                            numRequests = requests.length;

                            // click delete on the first component but press no
                            clickDelete(0, true);

                            // all components should still exist
                            expectComponents(getGroupElement(), allComponentsInGroup);

                            // no requests should have been sent to the server
                            expect(requests.length).toBe(numRequests);
                        });

                        it('shows a notification during the delete operation', function () {
                            var notificationSpy = EditHelpers.createNotificationSpy();
                            renderContainerPage(this, mockContainerXBlockHtml);
                            clickDelete(0);
                            EditHelpers.verifyNotificationShowing(notificationSpy, /Deleting/);
                            AjaxHelpers.respondWithJson(requests, {});
                            EditHelpers.verifyNotificationHidden(notificationSpy);
                        });

                        it('does not delete an xblock upon failure', function () {
                            var notificationSpy = EditHelpers.createNotificationSpy();
                            renderContainerPage(this, mockContainerXBlockHtml);
                            clickDelete(0);
                            EditHelpers.verifyNotificationShowing(notificationSpy, /Deleting/);
                            AjaxHelpers.respondWithError(requests);
                            EditHelpers.verifyNotificationShowing(notificationSpy, /Deleting/);
                            expectComponents(getGroupElement(), allComponentsInGroup);
                        });
                    });

                    describe("Duplicating an xblock", function () {
                        var clickDuplicate, duplicateComponentWithSuccess,
                            refreshXBlockSpies;

                        clickDuplicate = function (componentIndex) {

                            // find all duplicate buttons for the given group
                            var duplicateButtons = getGroupElement().find(".duplicate-button");
                            expect(duplicateButtons.length).toBe(NUM_COMPONENTS_PER_GROUP);

                            // click the requested duplicate button
                            duplicateButtons[componentIndex].click();
                        };

                        duplicateComponentWithSuccess = function (componentIndex) {
                            refreshXBlockSpies = spyOn(containerPage, "refreshXBlock");

                            clickDuplicate(componentIndex);

                            // verify content of request
                            AjaxHelpers.expectJsonRequest(requests, 'POST', '/xblock/', {
                                'duplicate_source_locator': 'locator-component-' + GROUP_TO_TEST + (componentIndex + 1),
                                'parent_locator': 'locator-group-' + GROUP_TO_TEST
                            });

                            // send the response
                            AjaxHelpers.respondWithJson(requests, {
                                'locator': 'locator-duplicated-component'
                            });

                            // expect parent container to be refreshed
                            expect(refreshXBlockSpies).toHaveBeenCalled();
                        };

                        it("can duplicate the first xblock", function () {
                            renderContainerPage(this, mockContainerXBlockHtml);
                            duplicateComponentWithSuccess(0);
                        });

                        it("can duplicate a middle xblock", function () {
                            renderContainerPage(this, mockContainerXBlockHtml);
                            duplicateComponentWithSuccess(1);
                        });

                        it("can duplicate the last xblock", function () {
                            renderContainerPage(this, mockContainerXBlockHtml);
                            duplicateComponentWithSuccess(NUM_COMPONENTS_PER_GROUP - 1);
                        });

                        it("can duplicate an xblock with broken JavaScript", function () {
                            renderContainerPage(this, mockBadContainerXBlockHtml);
                            containerPage.$('.duplicate-button').first().click();
                            AjaxHelpers.expectJsonRequest(requests, 'POST', '/xblock/', {
                                'duplicate_source_locator': 'locator-broken-javascript',
                                'parent_locator': 'locator-container'
                            });
                        });

                        it('shows a notification when duplicating', function () {
                            var notificationSpy = EditHelpers.createNotificationSpy();
                            renderContainerPage(this, mockContainerXBlockHtml);
                            clickDuplicate(0);
                            EditHelpers.verifyNotificationShowing(notificationSpy, /Duplicating/);
                            AjaxHelpers.respondWithJson(requests, {"locator": "new_item"});
                            EditHelpers.verifyNotificationHidden(notificationSpy);
                        });

                        it('does not duplicate an xblock upon failure', function () {
                            var notificationSpy = EditHelpers.createNotificationSpy();
                            renderContainerPage(this, mockContainerXBlockHtml);
                            refreshXBlockSpies = spyOn(containerPage, "refreshXBlock");
                            clickDuplicate(0);
                            EditHelpers.verifyNotificationShowing(notificationSpy, /Duplicating/);
                            AjaxHelpers.respondWithError(requests);
                            expectComponents(getGroupElement(), allComponentsInGroup);
                            expect(refreshXBlockSpies).not.toHaveBeenCalled();
                            EditHelpers.verifyNotificationShowing(notificationSpy, /Duplicating/);
                        });
                    });

                    describe("Previews", function () {

                        var getButtonIcon, getButtonText;

                        getButtonIcon = function (containerPage) {
                            return containerPage.$('.action-toggle-preview i');
                        };

                        getButtonText = function (containerPage) {
                            return containerPage.$('.action-toggle-preview .preview-text').text().trim();
                        };

                        if (pagedSpecificTests) {
                            it('has no text on the preview button to start with', function () {
                                containerPage = getContainerPage();
                                expect(getButtonIcon(containerPage)).toHaveClass('fa-refresh');
                                expect(getButtonIcon(containerPage).parent()).toHaveClass('is-hidden');
                                expect(getButtonText(containerPage)).toBe("");
                            });

                            function updatePreviewButtonTest(show_previews, expected_text) {
                                it('can set preview button to "' + expected_text + '"', function () {
                                    containerPage = getContainerPage();
                                    containerPage.updatePreviewButton(show_previews);
                                    expect(getButtonText(containerPage)).toBe(expected_text);
                                });
                            }

                            updatePreviewButtonTest(true, 'Hide Previews');
                            updatePreviewButtonTest(false, 'Show Previews');

                            it('triggers underlying view togglePreviews when preview button clicked', function () {
                                containerPage = getContainerPage();
                                containerPage.render();
                                spyOn(containerPage.xblockView, 'togglePreviews');

                                containerPage.$('.toggle-preview-button').click();
                                expect(containerPage.xblockView.togglePreviews).toHaveBeenCalled();
                            });
                        }
                    });

                    describe('createNewComponent ', function () {
                        var clickNewComponent;

                        clickNewComponent = function (index) {
                            containerPage.$(".new-component .new-component-type a.single-template")[index].click();
                        };

                        it('Attaches a handler to new component button', function() {
                            containerPage = getContainerPage();
                            containerPage.render();
                            // Stub jQuery.scrollTo module.
                            $.scrollTo = jasmine.createSpy('jQuery.scrollTo');
                            containerPage.$('.new-component-button').click();
                            expect($.scrollTo).toHaveBeenCalled();
                        });

                        it('sends the correct JSON to the server', function () {
                            renderContainerPage(this, mockContainerXBlockHtml);
                            clickNewComponent(0);
                            EditHelpers.verifyXBlockRequest(requests, {
                                "category": "discussion",
                                "type": "discussion",
                                "parent_locator": "locator-group-A"
                            });
                        });

                        it('shows a notification while creating', function () {
                            var notificationSpy = EditHelpers.createNotificationSpy();
                            renderContainerPage(this, mockContainerXBlockHtml);
                            clickNewComponent(0);
                            EditHelpers.verifyNotificationShowing(notificationSpy, /Adding/);
                            AjaxHelpers.respondWithJson(requests, { });
                            EditHelpers.verifyNotificationHidden(notificationSpy);
                        });

                        it('does not insert component upon failure', function () {
                            var requestCount;
                            renderContainerPage(this, mockContainerXBlockHtml);
                            clickNewComponent(0);
                            requestCount = requests.length;
                            AjaxHelpers.respondWithError(requests);
                            // No new requests should be made to refresh the view
                            expect(requests.length).toBe(requestCount);
                            expectComponents(getGroupElement(), allComponentsInGroup);
                        });

                        describe('Template Picker', function () {
                            var showTemplatePicker, verifyCreateHtmlComponent;

                            showTemplatePicker = function () {
                                containerPage.$('.new-component .new-component-type a.multiple-templates')[0].click();
                            };

                            verifyCreateHtmlComponent = function (test, templateIndex, expectedRequest) {
                                var xblockCount;
                                renderContainerPage(test, mockContainerXBlockHtml);
                                showTemplatePicker();
                                xblockCount = containerPage.$('.studio-xblock-wrapper').length;
                                containerPage.$('.new-component-html a')[templateIndex].click();
                                EditHelpers.verifyXBlockRequest(requests, expectedRequest);
                                AjaxHelpers.respondWithJson(requests, {"locator": "new_item"});
                                respondWithHtml(mockXBlockHtml);
                                expect(containerPage.$('.studio-xblock-wrapper').length).toBe(xblockCount + 1);
                            };

                            it('can add an HTML component without a template', function () {
                                verifyCreateHtmlComponent(this, 0, {
                                    "category": "html",
                                    "parent_locator": "locator-group-A"
                                });
                            });

                            it('can add an HTML component with a template', function () {
                                verifyCreateHtmlComponent(this, 1, {
                                    "category": "html",
                                    "boilerplate": "announcement.yaml",
                                    "parent_locator": "locator-group-A"
                                });
                            });
                        });
                    });
                });

            });
        }

        // Create a suite for a non-paged container that includes 'edit visibility' buttons
        parameterized_suite("Non paged",
            { },
            {
                page: ContainerPage,
                initial: 'mock/mock-container-xblock.underscore',
                add_response: 'mock/mock-xblock.underscore',
                has_visibility_editor: true,
                paged_specific_tests: false
            }
        );

        // Create a suite for a paged container that does not include 'edit visibility' buttons
        parameterized_suite("Paged",
            { page_size: 42 },
            {
                page: PagedContainerPage,
                initial: 'mock/mock-container-paged-xblock.underscore',
                add_response: 'mock/mock-xblock-paged.underscore',
                has_visibility_editor: false,
                paged_specific_tests: true
            }
        );
    });
