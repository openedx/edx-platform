define(["jquery", "underscore", "underscore.string", "js/spec_helpers/create_sinon", "js/spec_helpers/edit_helpers",
        "js/views/pages/container", "js/models/xblock_info", "jquery.simulate"],
    function ($, _, str, create_sinon, edit_helpers, ContainerPage, XBlockInfo) {

        describe("ContainerPage", function() {
            var lastRequest, renderContainerPage, expectComponents, respondWithHtml,
                model, containerPage, requests, initialDisplayName,
                mockContainerPage = readFixtures('mock/mock-container-page.underscore'),
                mockContainerXBlockHtml = readFixtures('mock/mock-container-xblock.underscore'),
                mockUpdatedContainerXBlockHtml = readFixtures('mock/mock-updated-container-xblock.underscore'),
                mockXBlockEditorHtml = readFixtures('mock/mock-xblock-editor.underscore');

            beforeEach(function () {
                var newDisplayName = 'New Display Name';

                edit_helpers.installEditTemplates();
                edit_helpers.installTemplate('xblock-string-field-editor');
                appendSetFixtures(mockContainerPage);

                edit_helpers.installMockXBlock({
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

            afterEach(function() {
                edit_helpers.uninstallMockXBlock();
            });

            lastRequest = function() { return requests[requests.length - 1]; };

            respondWithHtml = function(html) {
                var requestIndex = requests.length - 1;
                create_sinon.respondWithJson(
                    requests,
                    { html: html, "resources": [] },
                    requestIndex
                );
            };

            renderContainerPage = function(test, html, options) {
                requests = create_sinon.requests(test);
                containerPage = new ContainerPage(_.extend(options || {}, {
                    model: model,
                    templates: edit_helpers.mockComponentTemplates,
                    el: $('#content')
                }));
                containerPage.render();
                respondWithHtml(html);
            };

            expectComponents = function (container, locators) {
                // verify expected components (in expected order) by their locators
                var components = $(container).find('.studio-xblock-wrapper');
                expect(components.length).toBe(locators.length);
                _.each(locators, function(locator, locator_index) {
                    expect($(components[locator_index]).data('locator')).toBe(locator);
                });
            };

            describe("Initial display", function() {
                it('can render itself', function() {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    expect(containerPage.$('.xblock-header').length).toBe(9);
                    expect(containerPage.$('.wrapper-xblock .level-nesting')).not.toHaveClass('is-hidden');
                });

                it('shows a loading indicator', function() {
                    requests = create_sinon.requests(this);
                    containerPage.render();
                    expect(containerPage.$('.ui-loading')).not.toHaveClass('is-hidden');
                    respondWithHtml(mockContainerXBlockHtml);
                    expect(containerPage.$('.ui-loading')).toHaveClass('is-hidden');
                });

                it('inline edits the display name when performing a new action', function() {
                    renderContainerPage(this, mockContainerXBlockHtml, {
                        action: 'new'
                    });
                    expect(containerPage.$('.xblock-header').length).toBe(9);
                    expect(containerPage.$('.wrapper-xblock .level-nesting')).not.toHaveClass('is-hidden');
                    expect(containerPage.$('.xblock-field-input')).not.toHaveClass('is-hidden');
                });
            });

            describe("Editing the container", function() {
                var updatedDisplayName = 'Updated Test Container',
                    getDisplayNameWrapper;

                afterEach(function() {
                    edit_helpers.cancelModalIfShowing();
                });

                getDisplayNameWrapper = function() {
                    return containerPage.$('.wrapper-xblock-field');
                };

                it('can edit itself', function() {
                    var editButtons, displayNameElement;
                    renderContainerPage(this, mockContainerXBlockHtml);
                    displayNameElement = containerPage.$('.page-header-title');

                    // Click the root edit button
                    editButtons = containerPage.$('.nav-actions .edit-button');
                    editButtons.first().click();

                    // Expect a request to be made to show the studio view for the container
                    expect(str.startsWith(lastRequest().url, '/xblock/locator-container/studio_view')).toBeTruthy();
                    create_sinon.respondWithJson(requests, {
                        html: mockContainerXBlockHtml,
                        resources: []
                    });
                    expect(edit_helpers.isShowingModal()).toBeTruthy();

                    // Expect the correct title to be shown
                    expect(edit_helpers.getModalTitle()).toBe('Editing: Test Container');

                    // Press the save button and respond with a success message to the save
                    edit_helpers.pressModalButton('.action-save');
                    create_sinon.respondWithJson(requests, { });
                    expect(edit_helpers.isShowingModal()).toBeFalsy();

                    // Expect the last request be to refresh the container page
                    expect(str.startsWith(lastRequest().url,
                        '/xblock/locator-container/container_preview')).toBeTruthy();
                    create_sinon.respondWithJson(requests, {
                        html: mockUpdatedContainerXBlockHtml,
                        resources: []
                    });

                    // Expect the title to have been updated
                    expect(displayNameElement.text().trim()).toBe(updatedDisplayName);
                });

                it('can inline edit the display name', function() {
                    var displayNameInput, displayNameWrapper;
                    renderContainerPage(this, mockContainerXBlockHtml);
                    displayNameWrapper = getDisplayNameWrapper();
                    displayNameInput = edit_helpers.inlineEdit(displayNameWrapper, updatedDisplayName);
                    displayNameInput.change();
                    // This is the response for the change operation.
                    create_sinon.respondWithJson(requests, { });
                    // This is the response for the subsequent fetch operation.
                    create_sinon.respondWithJson(requests, {"display_name":  updatedDisplayName});
                    edit_helpers.verifyInlineEditChange(displayNameWrapper, updatedDisplayName);
                    expect(containerPage.model.get('display_name')).toBe(updatedDisplayName);
                });
            });

            describe("Editing an xblock", function() {
                afterEach(function() {
                    edit_helpers.cancelModalIfShowing();
                });

                it('can show an edit modal for a child xblock', function() {
                    var editButtons;
                    renderContainerPage(this, mockContainerXBlockHtml);
                    editButtons = containerPage.$('.wrapper-xblock .edit-button');
                    // The container should have rendered six mock xblocks
                    expect(editButtons.length).toBe(6);
                    editButtons[0].click();
                    // Make sure that the correct xblock is requested to be edited
                    expect(str.startsWith(lastRequest().url, '/xblock/locator-component-A1/studio_view')).toBeTruthy();
                    create_sinon.respondWithJson(requests, {
                        html: mockXBlockEditorHtml,
                        resources: []
                    });
                    expect(edit_helpers.isShowingModal()).toBeTruthy();
                });
            });

            describe("Editing an xmodule", function() {
                var mockXModuleEditor = readFixtures('mock/mock-xmodule-editor.underscore'),
                    newDisplayName = 'New Display Name';

                beforeEach(function () {
                    edit_helpers.installMockXModule({
                        data: "<p>Some HTML</p>",
                        metadata: {
                            display_name: newDisplayName
                        }
                    });
                });

                afterEach(function() {
                    edit_helpers.uninstallMockXModule();
                    edit_helpers.cancelModalIfShowing();
                });

                it('can save changes to settings', function() {
                    var editButtons, modal, mockUpdatedXBlockHtml;
                    mockUpdatedXBlockHtml = readFixtures('mock/mock-updated-xblock.underscore');
                    renderContainerPage(this, mockContainerXBlockHtml);
                    editButtons = containerPage.$('.wrapper-xblock .edit-button');
                    // The container should have rendered six mock xblocks
                    expect(editButtons.length).toBe(6);
                    editButtons[0].click();
                    create_sinon.respondWithJson(requests, {
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
                    create_sinon.respondWithJson(requests, {
                        id: model.id
                    });

                    // Respond to the request to refresh
                    respondWithHtml(mockUpdatedXBlockHtml);

                    // Verify that the xblock was updated
                    expect(containerPage.$('.mock-updated-content').text()).toBe('Mock Update');
                });
            });

            describe("xblock operations", function() {
                var getGroupElement,
                    NUM_COMPONENTS_PER_GROUP = 3, GROUP_TO_TEST = "A",
                    allComponentsInGroup = _.map(
                        _.range(NUM_COMPONENTS_PER_GROUP),
                        function(index) { return 'locator-component-' + GROUP_TO_TEST + (index + 1); }
                    );

                getGroupElement = function() {
                    return containerPage.$("[data-locator='locator-group-" + GROUP_TO_TEST + "']");
                };

                describe("Deleting an xblock", function() {
                    var clickDelete, deleteComponent, deleteComponentWithSuccess,
                        promptSpy;

                    beforeEach(function() {
                        promptSpy = edit_helpers.createPromptSpy();
                    });

                    clickDelete = function(componentIndex, clickNo) {

                        // find all delete buttons for the given group
                        var deleteButtons = getGroupElement().find(".delete-button");
                        expect(deleteButtons.length).toBe(NUM_COMPONENTS_PER_GROUP);

                        // click the requested delete button
                        deleteButtons[componentIndex].click();

                        // click the 'yes' or 'no' button in the prompt
                        edit_helpers.confirmPrompt(promptSpy, clickNo);
                    };

                    deleteComponent = function(componentIndex) {
                        clickDelete(componentIndex);
                        create_sinon.respondWithJson(requests, {});

                        // first request contains given component's id (to delete the component)
                        expect(requests[requests.length - 2].url).toMatch(
                            new RegExp("locator-component-" + GROUP_TO_TEST + (componentIndex + 1))
                        );

                        // final request to refresh the xblock info
                        create_sinon.expectJsonRequest(requests, 'GET', '/xblock/locator-container');
                    };

                    deleteComponentWithSuccess = function(componentIndex) {
                        deleteComponent(componentIndex);

                        // verify the new list of components within the group
                        expectComponents(
                            getGroupElement(),
                            _.without(allComponentsInGroup, allComponentsInGroup[componentIndex])
                        );
                    };

                    it("can delete the first xblock", function() {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        deleteComponentWithSuccess(0);
                    });

                    it("can delete a middle xblock", function() {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        deleteComponentWithSuccess(1);
                    });

                    it("can delete the last xblock", function() {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        deleteComponentWithSuccess(NUM_COMPONENTS_PER_GROUP - 1);
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

                    it('shows a notification during the delete operation', function() {
                        var notificationSpy = edit_helpers.createNotificationSpy();
                        renderContainerPage(this, mockContainerXBlockHtml);
                        clickDelete(0);
                        edit_helpers.verifyNotificationShowing(notificationSpy, /Deleting/);
                        create_sinon.respondWithJson(requests, {});
                        edit_helpers.verifyNotificationHidden(notificationSpy);
                    });

                    it('does not delete an xblock upon failure', function () {
                        var notificationSpy = edit_helpers.createNotificationSpy();
                        renderContainerPage(this, mockContainerXBlockHtml);
                        clickDelete(0);
                        edit_helpers.verifyNotificationShowing(notificationSpy, /Deleting/);
                        create_sinon.respondWithError(requests);
                        edit_helpers.verifyNotificationShowing(notificationSpy, /Deleting/);
                        expectComponents(getGroupElement(), allComponentsInGroup);
                    });
                });

                describe("Duplicating an xblock", function() {
                    var clickDuplicate, duplicateComponentWithSuccess,
                        refreshXBlockSpies;

                    clickDuplicate = function(componentIndex) {

                        // find all duplicate buttons for the given group
                        var duplicateButtons = getGroupElement().find(".duplicate-button");
                        expect(duplicateButtons.length).toBe(NUM_COMPONENTS_PER_GROUP);

                        // click the requested duplicate button
                        duplicateButtons[componentIndex].click();
                    };

                    duplicateComponentWithSuccess = function(componentIndex) {
                        refreshXBlockSpies = spyOn(containerPage, "refreshXBlock");

                        clickDuplicate(componentIndex);

                        // verify content of request
                        create_sinon.expectJsonRequest(requests, 'POST', '/xblock/', {
                            'duplicate_source_locator': 'locator-component-' + GROUP_TO_TEST + (componentIndex + 1),
                            'parent_locator': 'locator-group-' + GROUP_TO_TEST
                        });

                        // send the response
                        create_sinon.respondWithJson(requests, {
                            'locator': 'locator-duplicated-component'
                        });

                        // expect parent container to be refreshed
                        expect(refreshXBlockSpies).toHaveBeenCalled();
                    };

                    it("can duplicate the first xblock", function() {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        duplicateComponentWithSuccess(0);
                    });

                    it("can duplicate a middle xblock", function() {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        duplicateComponentWithSuccess(1);
                    });

                    it("can duplicate the last xblock", function() {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        duplicateComponentWithSuccess(NUM_COMPONENTS_PER_GROUP - 1);
                    });

                    it('shows a notification when duplicating', function () {
                        var notificationSpy = edit_helpers.createNotificationSpy();
                        renderContainerPage(this, mockContainerXBlockHtml);
                        clickDuplicate(0);
                        edit_helpers.verifyNotificationShowing(notificationSpy, /Duplicating/);
                        create_sinon.respondWithJson(requests, {"locator": "new_item"});
                        edit_helpers.verifyNotificationHidden(notificationSpy);
                    });

                    it('does not duplicate an xblock upon failure', function () {
                        var notificationSpy = edit_helpers.createNotificationSpy();
                        renderContainerPage(this, mockContainerXBlockHtml);
                        refreshXBlockSpies = spyOn(containerPage, "refreshXBlock");
                        clickDuplicate(0);
                        edit_helpers.verifyNotificationShowing(notificationSpy, /Duplicating/);
                        create_sinon.respondWithError(requests);
                        expectComponents(getGroupElement(), allComponentsInGroup);
                        expect(refreshXBlockSpies).not.toHaveBeenCalled();
                        edit_helpers.verifyNotificationShowing(notificationSpy, /Duplicating/);
                    });
                });

                describe('createNewComponent ', function () {
                    var clickNewComponent;

                    clickNewComponent = function (index) {
                        containerPage.$(".new-component .new-component-type a.single-template")[index].click();
                    };

                    it('sends the correct JSON to the server', function () {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        clickNewComponent(0);
                        edit_helpers.verifyXBlockRequest(requests, {
                            "category": "discussion",
                            "type": "discussion",
                            "parent_locator": "locator-group-A"
                        });
                    });

                    it('shows a notification while creating', function () {
                        var notificationSpy = edit_helpers.createNotificationSpy();
                        renderContainerPage(this, mockContainerXBlockHtml);
                        clickNewComponent(0);
                        edit_helpers.verifyNotificationShowing(notificationSpy, /Adding/);
                        create_sinon.respondWithJson(requests, { });
                        edit_helpers.verifyNotificationHidden(notificationSpy);
                    });

                    it('does not insert component upon failure', function () {
                        var requestCount;
                        renderContainerPage(this, mockContainerXBlockHtml);
                        clickNewComponent(0);
                        requestCount = requests.length;
                        create_sinon.respondWithError(requests);
                        // No new requests should be made to refresh the view
                        expect(requests.length).toBe(requestCount);
                        expectComponents(getGroupElement(), allComponentsInGroup);
                    });

                    describe('Template Picker', function() {
                        var showTemplatePicker, verifyCreateHtmlComponent,
                            mockXBlockHtml = readFixtures('mock/mock-xblock.underscore');

                        showTemplatePicker = function() {
                            containerPage.$('.new-component .new-component-type a.multiple-templates')[0].click();
                        };

                        verifyCreateHtmlComponent = function(test, templateIndex, expectedRequest) {
                            var xblockCount;
                            renderContainerPage(test, mockContainerXBlockHtml);
                            showTemplatePicker();
                            xblockCount = containerPage.$('.studio-xblock-wrapper').length;
                            containerPage.$('.new-component-html a')[templateIndex].click();
                            edit_helpers.verifyXBlockRequest(requests, expectedRequest);
                            create_sinon.respondWithJson(requests, {"locator": "new_item"});
                            respondWithHtml(mockXBlockHtml);
                            expect(containerPage.$('.studio-xblock-wrapper').length).toBe(xblockCount + 1);
                        };

                        it('can add an HTML component without a template', function() {
                            verifyCreateHtmlComponent(this, 0, {
                                "category": "html",
                                "parent_locator": "locator-group-A"
                            });
                        });

                        it('can add an HTML component with a template', function() {
                            verifyCreateHtmlComponent(this, 1, {
                                "category": "html",
                                "boilerplate" : "announcement.yaml",
                                "parent_locator": "locator-group-A"
                            });
                        });
                    });
                });
            });
        });
    });
