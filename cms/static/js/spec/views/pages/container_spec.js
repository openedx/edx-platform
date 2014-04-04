define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/edit_helpers",
    "js/views/feedback_notification", "js/views/feedback_prompt",
    "js/views/pages/container", "js/models/xblock_info"],
    function ($, create_sinon, edit_helpers, Notification, Prompt, ContainerPage, XBlockInfo) {

        describe("ContainerPage", function() {
            var lastRequest, renderContainerPage, expectComponents, respondWithHtml,
                model, containerPage, requests,
                mockContainerPage = readFixtures('mock/mock-container-page.underscore'),
                ABTestFixture = readFixtures('mock/mock-container-xblock.underscore');

            beforeEach(function () {
                edit_helpers.installEditTemplates();
                appendSetFixtures(mockContainerPage);

                model = new XBlockInfo({
                    id: 'testCourse/branch/draft/block/verticalFFF',
                    display_name: 'Test Unit',
                    category: 'vertical'
                });
                containerPage = new ContainerPage({
                    model: model,
                    el: $('#content')
                });
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

            renderContainerPage = function(html, that) {
                requests = create_sinon.requests(that);
                containerPage.render();
                respondWithHtml(html);
            };

            expectComponents = function (container, locators) {
                // verify expected components (in expected order) by their locators
                var components = $(container).find('[data-locator]');
                expect(components.length).toBe(locators.length);
                _.each(locators, function(locator, locator_index) {
                    expect($(components[locator_index]).data('locator')).toBe(locator);
                });
            };

            describe("Basic display", function() {
                var mockContainerXBlockHtml = readFixtures('mock/mock-container-xblock.underscore');

                it('can render itself', function() {
                    renderContainerPage(mockContainerXBlockHtml, this);
                    expect(containerPage.$el.select('.xblock-header')).toBeTruthy();
                    expect(containerPage.$('.wrapper-xblock')).not.toHaveClass('is-hidden');
                    expect(containerPage.$('.no-container-content')).toHaveClass('is-hidden');
                });
                it('shows a loading indicator', function() {
                    requests = create_sinon.requests(this);
                    containerPage.render();
                    expect(containerPage.$('.ui-loading')).not.toHaveClass('is-hidden');
                    respondWithHtml(mockContainerXBlockHtml);
                    expect(containerPage.$('.ui-loading')).toHaveClass('is-hidden');
                });
            });

            describe("Editing an xblock", function() {
                var mockContainerXBlockHtml,
                    mockXBlockEditorHtml,
                    newDisplayName = 'New Display Name';

                beforeEach(function () {
                    edit_helpers.installMockXBlock({
                        data: "<p>Some HTML</p>",
                        metadata: {
                            display_name: newDisplayName
                        }
                    });
                });

                afterEach(function() {
                    edit_helpers.uninstallMockXBlock();
                    edit_helpers.cancelModalIfShowing();
                });

                mockContainerXBlockHtml = readFixtures('mock/mock-container-xblock.underscore');
                mockXBlockEditorHtml = readFixtures('mock/mock-xblock-editor.underscore');

                it('can show an edit modal for a child xblock', function() {
                    var editButtons;
                    renderContainerPage(mockContainerXBlockHtml, this);
                    editButtons = containerPage.$('.edit-button');
                    // The container renders six mock xblocks, so there should be an equal number of edit buttons
                    expect(editButtons.length).toBe(6);
                    editButtons.first().click();
                    // Make sure that the correct xblock is requested to be edited
                    expect(lastRequest().url).toBe(
                        '/xblock/locator-component-A1/studio_view'
                    );
                    create_sinon.respondWithJson(requests, {
                        html: mockXBlockEditorHtml,
                        resources: []
                    });
                    expect(edit_helpers.isShowingModal()).toBeTruthy();
                });

                it('can save changes to settings', function() {
                    var editButtons, modal, mockUpdatedXBlockHtml;
                    mockUpdatedXBlockHtml = readFixtures('mock/mock-updated-xblock.underscore');
                    renderContainerPage(mockContainerXBlockHtml, this);
                    editButtons = containerPage.$('.edit-button');
                    // The container renders six mock xblocks, so there should be an equal number of edit buttons
                    expect(editButtons.length).toBe(6);
                    editButtons.first().click();
                    create_sinon.respondWithJson(requests, {
                        html: mockXBlockEditorHtml,
                        resources: []
                    });

                    modal = $('.edit-xblock-modal');
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

            describe("Empty container", function() {
                var mockContainerXBlockHtml = readFixtures('mock/mock-empty-container-xblock.underscore');

                it('shows the "no children" message', function() {
                    renderContainerPage(mockContainerXBlockHtml, this);
                    expect(containerPage.$('.no-container-content')).not.toHaveClass('is-hidden');
                    expect(containerPage.$('.wrapper-xblock')).toHaveClass('is-hidden');
                });
            });

            describe("xblock operations", function() {
                var getGroupElement, expectNumComponents, expectNotificationToBeShown,
                    NUM_GROUPS = 2, NUM_COMPONENTS_PER_GROUP = 3, GROUP_TO_TEST = "A",
                    notificationSpies,
                    allComponentsInGroup = _.map(
                        _.range(NUM_COMPONENTS_PER_GROUP),
                        function(index) { return 'locator-component-' + GROUP_TO_TEST + (index + 1); }
                    );

                beforeEach(function () {
                    notificationSpies = spyOnConstructor(Notification, "Mini", ["show", "hide"]);
                    notificationSpies.show.andReturn(notificationSpies);
                });

                getGroupElement = function() {
                    return containerPage.$("[data-locator='locator-group-" + GROUP_TO_TEST + "']");
                };
                expectNumComponents = function(numComponents) {
                    expect(containerPage.$('.wrapper-xblock.level-element').length).toBe(
                        numComponents * NUM_GROUPS
                    );
                };
                expectNotificationToBeShown = function(expectedTitle) {
                    expect(notificationSpies.constructor).toHaveBeenCalled();
                    expect(notificationSpies.show).toHaveBeenCalled();
                    expect(notificationSpies.hide).not.toHaveBeenCalled();
                    expect(notificationSpies.constructor.mostRecentCall.args[0].title).toMatch(expectedTitle);
                };

                describe("Deleting an xblock", function() {
                    var clickDelete, deleteComponent, deleteComponentWithSuccess,
                        promptSpies;

                    beforeEach(function() {
                        promptSpies = spyOnConstructor(Prompt, "Warning", ["show", "hide"]);
                        promptSpies.show.andReturn(this.promptSpies);
                    });

                    clickDelete = function(componentIndex) {

                        // find all delete buttons for the given group
                        var deleteButtons = getGroupElement().find(".delete-button");
                        expect(deleteButtons.length).toBe(NUM_COMPONENTS_PER_GROUP);

                        // click the requested delete button
                        deleteButtons[componentIndex].click();

                        // expect delete confirmation
                        expect(promptSpies.constructor).toHaveBeenCalled();

                        // no components should be deleted yet
                        expectNumComponents(NUM_COMPONENTS_PER_GROUP);
                    };

                    deleteComponent = function(componentIndex, responseCode) {

                        // click delete button for given component
                        clickDelete(componentIndex);

                        // click 'Yes' on delete confirmation
                        promptSpies.constructor.mostRecentCall.args[0].actions.primary.click(promptSpies);

                        // expect 'deleting' notification to be shown
                        expectNotificationToBeShown(/Deleting/);

                        // respond to request with given response code
                        lastRequest().respond(responseCode, {}, "");

                        // expect request URL to contain given component's id
                        expect(lastRequest().url).toMatch(
                            new RegExp("locator-component-" + GROUP_TO_TEST + (componentIndex + 1))
                        );
                    };

                    deleteComponentWithSuccess = function(componentIndex) {

                        // delete component with an 'OK' response code
                        deleteComponent(componentIndex, 200);

                        // expect 'deleting' notification to be hidden
                        expect(notificationSpies.hide).toHaveBeenCalled();

                        // verify the new list of components within the group
                        expectComponents(
                            getGroupElement(),
                            _.without(allComponentsInGroup, allComponentsInGroup[componentIndex])
                        );
                    };

                    it("deletes first xblock", function() {
                        renderContainerPage(ABTestFixture, this);
                        deleteComponentWithSuccess(0);
                    });

                    it("deletes middle xblock", function() {
                        renderContainerPage(ABTestFixture, this);
                        deleteComponentWithSuccess(1);
                    });

                    it("deletes last xblock", function() {
                        renderContainerPage(ABTestFixture, this);
                        deleteComponentWithSuccess(NUM_COMPONENTS_PER_GROUP - 1);
                    });

                    it('does not delete xblock when clicking No in prompt', function () {
                        var numRequests;

                        renderContainerPage(ABTestFixture, this);
                        numRequests = requests.length;

                        // click delete on the first component
                        clickDelete(0);

                        // click 'No' on delete confirmation
                        promptSpies.constructor.mostRecentCall.args[0].actions.secondary.click(promptSpies);

                        // all components should still exist
                        expectComponents(getGroupElement(), allComponentsInGroup);

                        // no requests should have been sent to the server
                        expect(requests.length).toBe(numRequests);
                    });

                    it('does not delete xblock upon failure', function () {
                        renderContainerPage(ABTestFixture, this);
                        deleteComponent(0, 500);
                        expectComponents(getGroupElement(), allComponentsInGroup);
                        expect(notificationSpies.hide).not.toHaveBeenCalled();
                    });
                });

                describe("Duplicating an xblock", function() {
                    var clickDuplicate, duplicateComponentWithResponse, duplicateComponentWithSuccess,
                        refreshXBlockSpies;

                    beforeEach(function() {
                        refreshXBlockSpies = spyOn(containerPage, "refreshXBlock");
                    });

                    clickDuplicate = function(componentIndex) {

                        // find all duplicate buttons for the given group
                        var duplicateButtons = getGroupElement().find(".duplicate-button");
                        expect(duplicateButtons.length).toBe(NUM_COMPONENTS_PER_GROUP);

                        // click the requested duplicate button
                        duplicateButtons[componentIndex].click();
                    };

                    duplicateComponentWithResponse = function(componentIndex, responseCode) {
                        var request;

                        // click duplicate button for given component
                        clickDuplicate(componentIndex);

                        // expect 'duplicating' notification to be shown
                        expectNotificationToBeShown(/Duplicating/);

                        // verify content of request
                        request = lastRequest();
                        request.respond(
                            responseCode,
                            { "Content-Type": "application/json" },
                            JSON.stringify({'locator': 'locator-duplicated-component'})
                        );
                        expect(request.url).toEqual("/xblock");
                        expect(request.method).toEqual("POST");
                        expect(JSON.parse(request.requestBody)).toEqual(
                            JSON.parse(
                                '{' +
                                    '"duplicate_source_locator": "locator-component-' + GROUP_TO_TEST + (componentIndex + 1) + '",' +
                                    '"parent_locator": "locator-group-' + GROUP_TO_TEST +
                                    '"}'
                            )
                        );
                    };

                    duplicateComponentWithSuccess = function(componentIndex) {

                        // duplicate component with an 'OK' response code
                        duplicateComponentWithResponse(componentIndex, 200);

                        // expect 'duplicating' notification to be hidden
                        expect(notificationSpies.hide).toHaveBeenCalled();

                        // expect parent container to be refreshed
                        expect(refreshXBlockSpies).toHaveBeenCalled();
                    };

                    it("duplicates first xblock", function() {
                        renderContainerPage(ABTestFixture, this);
                        duplicateComponentWithSuccess(0);
                    });

                    it("duplicates middle xblock", function() {
                        renderContainerPage(ABTestFixture, this);
                        duplicateComponentWithSuccess(1);
                    });

                    it("duplicates last xblock", function() {
                        renderContainerPage(ABTestFixture, this);
                        duplicateComponentWithSuccess(NUM_COMPONENTS_PER_GROUP - 1);
                    });

                    it('does not duplicate xblock upon failure', function () {
                        renderContainerPage(ABTestFixture, this);
                        duplicateComponentWithResponse(0, 500);
                        expectComponents(getGroupElement(), allComponentsInGroup);
                        expect(notificationSpies.hide).not.toHaveBeenCalled();
                        expect(refreshXBlockSpies).not.toHaveBeenCalled();
                    });
                });
            });
        });
    });
