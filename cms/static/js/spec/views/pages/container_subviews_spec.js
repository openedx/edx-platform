define(["jquery", "underscore", "underscore.string", "js/spec_helpers/create_sinon", "js/spec_helpers/edit_helpers",
        "js/views/feedback_prompt", "js/views/pages/container", "js/views/pages/container_subviews",
        "js/models/xblock_info"],
    function ($, _, str, create_sinon, edit_helpers, Prompt, ContainerPage, ContainerSubviews, XBlockInfo) {

        describe("Container Subviews", function() {
            var model, containerPage, requests, createContainerPage, renderContainerPage,
                respondWithHtml, respondWithJson, fetch,
                disabledCss = "is-disabled", defaultXBlockInfo, createXBlockInfo,
                mockContainerPage = readFixtures('mock/mock-container-page.underscore'),
                mockContainerXBlockHtml = readFixtures('mock/mock-empty-container-xblock.underscore');

            beforeEach(function () {
                edit_helpers.installTemplate('xblock-string-field-editor');
                edit_helpers.installTemplate('publish-xblock');
                edit_helpers.installTemplate('publish-history');
                edit_helpers.installTemplate('unit-outline');
                edit_helpers.installTemplate('container-message');
                appendSetFixtures(mockContainerPage);
            });

            defaultXBlockInfo = {
                id: 'locator-container',
                display_name: 'Test Container',
                category: 'vertical',
                published: false,
                has_changes: false,
                edited_on: "Jul 02, 2014 at 14:20 UTC", edited_by: "joe",
                published_on: "Jul 01, 2014 at 12:45 UTC", published_by: "amako",
                visible_to_staff_only: false,
                currently_visible_to_students: false
            };

            createXBlockInfo = function(options) {
                return _.extend(_.extend({}, defaultXBlockInfo), options || {});
            };

            createContainerPage = function (test, options) {
                requests = create_sinon.requests(test);
                model = new XBlockInfo(createXBlockInfo(options), { parse: true });
                containerPage = new ContainerPage({
                    model: model,
                    templates: edit_helpers.mockComponentTemplates,
                    el: $('#content'),
                    isUnitPage: true
                });
            };

            renderContainerPage = function (test, html, options) {
                createContainerPage(test, options);
                containerPage.render();
                respondWithHtml(html);
            };

            respondWithHtml = function(html) {
                var requestIndex = requests.length - 1;
                create_sinon.respondWithJson(
                    requests,
                    { html: html, "resources": [] },
                    requestIndex
                );
            };

            respondWithJson = function(json, requestIndex) {
                create_sinon.respondWithJson(
                    requests,
                    json,
                    requestIndex
                );
            };

            fetch = function (json) {
                json = createXBlockInfo(json);
                model.fetch();
                respondWithJson(json);
            };

            describe("PreviewActionController", function () {
                var viewPublishedCss = '.button-view',
                    previewCss = '.button-preview';

                it('renders correctly for private unit', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    expect(containerPage.$(viewPublishedCss)).toHaveClass(disabledCss);
                    expect(containerPage.$(previewCss)).not.toHaveClass(disabledCss);
                });

                it('updates when published attribute changes', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"published": true});
                    expect(containerPage.$(viewPublishedCss)).not.toHaveClass(disabledCss);

                    fetch({"published": false});
                    expect(containerPage.$(viewPublishedCss)).toHaveClass(disabledCss);
                });

                it('updates when has_changes attribute changes', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"has_changes": true});
                    expect(containerPage.$(previewCss)).not.toHaveClass(disabledCss);

                    fetch({"published": true, "has_changes": false});
                    expect(containerPage.$(previewCss)).toHaveClass(disabledCss);

                    // If published is false, preview is always enabled.
                    fetch({"published": false, "has_changes": false});
                    expect(containerPage.$(previewCss)).not.toHaveClass(disabledCss);
                });
            });

            describe("Publisher", function () {
                var headerCss = '.pub-status',
                    bitPublishingCss = "div.bit-publishing",
                    publishedBit = "is-published",
                    draftBit = "is-draft",
                    staffOnlyBit = "is-staff-only",
                    publishButtonCss = ".action-publish",
                    discardChangesButtonCss = ".action-discard",
                    lastDraftCss = ".wrapper-last-draft",
                    releaseDateTitleCss = ".wrapper-release .title",
                    releaseDateContentCss = ".wrapper-release .copy",
                    promptSpies, sendDiscardChangesToServer;

                sendDiscardChangesToServer = function() {
                    // Helper function to do the discard operation, up until the server response.
                    containerPage.render();
                    respondWithHtml(mockContainerXBlockHtml);
                    fetch({"published": true, "has_changes": true});
                    expect(containerPage.$(discardChangesButtonCss)).not.toHaveClass('is-disabled');
                    expect(containerPage.$(bitPublishingCss)).toHaveClass(draftBit);
                    // Click discard changes
                    containerPage.$(discardChangesButtonCss).click();

                    // Confirm the discard.
                    expect(promptSpies.constructor).toHaveBeenCalled();
                    promptSpies.constructor.mostRecentCall.args[0].actions.primary.click(promptSpies);

                    create_sinon.expectJsonRequest(requests, "POST", "/xblock/locator-container",
                        {"publish": "discard_changes"}
                    );
                };

                beforeEach(function() {
                    promptSpies = spyOnConstructor(Prompt, "Warning", ["show", "hide"]);
                    promptSpies.show.andReturn(this.promptSpies);
                });

                it('renders correctly with private content', function () {
                    var verifyPrivateState = function() {
                        expect(containerPage.$(headerCss).text()).toContain('Draft (Never published)');
                        expect(containerPage.$(publishButtonCss)).not.toHaveClass(disabledCss);
                        expect(containerPage.$(discardChangesButtonCss)).toHaveClass(disabledCss);
                        expect(containerPage.$(bitPublishingCss)).not.toHaveClass(draftBit);
                        expect(containerPage.$(bitPublishingCss)).not.toHaveClass(publishedBit);
                    };
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"published": false, "has_changes": false});
                    verifyPrivateState();

                    fetch({"published": false, "has_changes": true});
                    verifyPrivateState();
                });

                it('renders correctly with public content', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"published": true, "has_changes": false});
                    expect(containerPage.$(headerCss).text()).toContain('Published');
                    expect(containerPage.$(publishButtonCss)).toHaveClass(disabledCss);
                    expect(containerPage.$(discardChangesButtonCss)).toHaveClass(disabledCss);
                    expect(containerPage.$(bitPublishingCss)).toHaveClass(publishedBit);

                    fetch({"published": true, "has_changes": true});
                    expect(containerPage.$(headerCss).text()).toContain('Draft (Unpublished changes)');
                    expect(containerPage.$(publishButtonCss)).not.toHaveClass(disabledCss);
                    expect(containerPage.$(discardChangesButtonCss)).not.toHaveClass(disabledCss);
                    expect(containerPage.$(bitPublishingCss)).toHaveClass(draftBit);
                });

                it('can publish private content', function () {
                    var notificationSpy = edit_helpers.createNotificationSpy();
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"published": false, "has_changes": false});
                    expect(containerPage.$(bitPublishingCss)).not.toHaveClass(draftBit);
                    expect(containerPage.$(bitPublishingCss)).not.toHaveClass(publishedBit);

                    // Click publish
                    containerPage.$(publishButtonCss).click();
                    edit_helpers.verifyNotificationShowing(notificationSpy, /Publishing/);

                    create_sinon.expectJsonRequest(requests, "POST", "/xblock/locator-container",
                        {"publish": "make_public"}
                    );

                    // Response to publish call
                    respondWithJson({"id": "locator-container", "data": null, "metadata":{}});
                    edit_helpers.verifyNotificationHidden(notificationSpy);

                    create_sinon.expectJsonRequest(requests, "GET", "/xblock/locator-container");
                    // Response to fetch
                    respondWithJson({"id": "locator-container", "published": true, "has_changes": false});

                    // Verify updates displayed
                    expect(containerPage.$(bitPublishingCss)).toHaveClass(publishedBit);
                    // Verify that the "published" value has been cleared out of the model.
                    expect(containerPage.model.get("publish")).toBeNull();
                });

                it('can does not fetch if publish fails', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"published": false});
                    expect(containerPage.$(bitPublishingCss)).not.toHaveClass(publishedBit);

                    // Click publish
                    containerPage.$(publishButtonCss).click();

                    var numRequests = requests.length;
                    // Respond with failure
                    create_sinon.respondWithError(requests);

                    expect(requests.length).toEqual(numRequests);

                    // Verify still in draft state.
                    expect(containerPage.$(bitPublishingCss)).not.toHaveClass(publishedBit);
                    // Verify that the "published" value has been cleared out of the model.
                    expect(containerPage.model.get("publish")).toBeNull();
                });

                it('can discard changes', function () {
                    var notificationSpy, renderPageSpy, numRequests;
                    createContainerPage(this);
                    notificationSpy = edit_helpers.createNotificationSpy();
                    renderPageSpy = spyOn(containerPage.xblockPublisher, 'renderPage').andCallThrough();

                    sendDiscardChangesToServer();
                    numRequests = requests.length;

                    // Respond with success.
                    respondWithJson({"id": "locator-container"});
                    edit_helpers.verifyNotificationHidden(notificationSpy);

                    // Verify other requests are sent to the server to update page state.
                    // Response to fetch, specifying the very next request (as multiple requests will be sent to server)
                    expect(requests.length > numRequests).toBeTruthy();
                    expect(containerPage.model.get("publish")).toBeNull();
                    expect(renderPageSpy).toHaveBeenCalled();
                });

                it('does not fetch if discard changes fails', function () {
                    var renderPageSpy, numRequests;
                    createContainerPage(this);
                    renderPageSpy = spyOn(containerPage.xblockPublisher, 'renderPage').andCallThrough();

                    sendDiscardChangesToServer();
                    numRequests = requests.length;

                    // Respond with failure
                    create_sinon.respondWithError(requests);

                    expect(requests.length).toEqual(numRequests);
                    expect(containerPage.$(discardChangesButtonCss)).not.toHaveClass('is-disabled');
                    expect(containerPage.model.get("publish")).toBeNull();
                    expect(renderPageSpy).not.toHaveBeenCalled();
                });

                it('does not discard changes on cancel', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"published": true, "has_changes": true});
                    var numRequests = requests.length;

                    // Click discard changes
                    containerPage.$(discardChangesButtonCss).click();

                    // Click cancel to confirmation.
                    expect(promptSpies.constructor).toHaveBeenCalled();
                    promptSpies.constructor.mostRecentCall.args[0].actions.secondary.click(promptSpies);

                    expect(requests.length).toEqual(numRequests);
                    expect(containerPage.$(discardChangesButtonCss)).not.toHaveClass('is-disabled');
                });

                it('renders the last published date and user when there are no changes', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"published_on": "Jul 01, 2014 at 12:45 UTC", "published_by": "amako"});
                    expect(containerPage.$(lastDraftCss).text()).
                        toContain("Last published Jul 01, 2014 at 12:45 UTC by amako");
                });

                it('renders the last saved date and user when there are changes', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({"has_changes": true, "edited_on": "Jul 02, 2014 at 14:20 UTC", "edited_by": "joe"});
                    expect(containerPage.$(lastDraftCss).text()).
                        toContain("Draft saved on Jul 02, 2014 at 14:20 UTC by joe");
                });

                describe("Release Date", function() {
                    it('renders correctly when unreleased', function () {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        fetch({"published": true, "released_to_students": false,
                            "release_date": "Jul 02, 2014 at 14:20 UTC", "release_date_from": 'Section "Week 1"'});
                        expect(containerPage.$(releaseDateTitleCss).text()).toContain("Scheduled:");
                        expect(containerPage.$(releaseDateContentCss).text()).
                            toContain('Jul 02, 2014 at 14:20 UTC with Section "Week 1"');
                    });

                    it('renders correctly when released', function () {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        fetch({"published": true, "released_to_students": true,
                            "release_date": "Jul 02, 2014 at 14:20 UTC", "release_date_from": 'Section "Week 1"' });
                        expect(containerPage.$(releaseDateTitleCss).text()).toContain("Released:");
                        expect(containerPage.$(releaseDateContentCss).text()).
                            toContain('Jul 02, 2014 at 14:20 UTC with Section "Week 1"');
                    });

                    it('renders correctly when the release date is not set', function () {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        fetch({"published": true, "released_to_students": false,
                            "release_date": null, "release_date_from": null });
                        expect(containerPage.$(releaseDateTitleCss).text()).toContain("Release:");
                        expect(containerPage.$(releaseDateContentCss).text()).toContain("Unscheduled");
                    });

                    it('renders correctly when the unit is not published', function () {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        fetch({"published": false, "released_to_students": true,
                            "release_date": "Jul 02, 2014 at 14:20 UTC", "release_date_from": 'Section "Week 1"' });
                        // Force a render because none of the fetched fields will trigger a render
                        containerPage.xblockPublisher.render();
                        expect(containerPage.$(releaseDateTitleCss).text()).toContain("Release:");
                        expect(containerPage.$(releaseDateContentCss).text()).
                            toContain('Jul 02, 2014 at 14:20 UTC with Section "Week 1"');
                    });
                });

                describe("Content Visibility", function () {
                    var requestStaffOnly, verifyStaffOnly, promptSpy;

                    requestStaffOnly = function(isStaffOnly) {
                        containerPage.$('.action-staff-lock').click();

                        // If removing the staff lock, click 'Yes' to confirm
                        if (!isStaffOnly) {
                            edit_helpers.confirmPrompt(promptSpy);
                        }

                        create_sinon.expectJsonRequest(requests, 'POST', '/xblock/locator-container', {
                            publish: 'republish',
                            metadata: { visible_to_staff_only: isStaffOnly }
                        });
                        create_sinon.respondWithJson(requests, {
                            data: null,
                            id: "locator-container",
                            metadata: {
                                visible_to_staff_only: isStaffOnly
                            }
                        });
                        create_sinon.expectJsonRequest(requests, 'GET', '/xblock/locator-container');
                        create_sinon.respondWithJson(requests, createXBlockInfo({
                            published: containerPage.model.get('published'),
                            visible_to_staff_only: isStaffOnly
                        }));
                    };

                    verifyStaffOnly = function(isStaffOnly) {
                        if (isStaffOnly) {
                            expect(containerPage.$('.action-staff-lock i')).toHaveClass('icon-check');
                            expect(containerPage.$('.wrapper-visibility .copy').text()).toBe('Staff Only');
                            expect(containerPage.$(bitPublishingCss)).toHaveClass(staffOnlyBit);
                        } else {
                            expect(containerPage.$('.action-staff-lock i')).toHaveClass('icon-check-empty');
                            expect(containerPage.$('.wrapper-visibility .copy').text()).toBe('Staff and Students');
                            expect(containerPage.$(bitPublishingCss)).not.toHaveClass(staffOnlyBit);
                        }
                    };

                    it("is initially shown to all", function() {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        verifyStaffOnly(false);
                    });

                    it("can be set to staff only", function() {
                        renderContainerPage(this, mockContainerXBlockHtml);
                        containerPage.$('.action-staff-lock').click();
                        requestStaffOnly(true);
                        verifyStaffOnly(true);
                    });

                    it("can remove staff only setting", function() {
                        promptSpy = edit_helpers.createPromptSpy();
                        renderContainerPage(this, mockContainerXBlockHtml);
                        requestStaffOnly(true);
                        requestStaffOnly(false);
                        verifyStaffOnly(false);
                        expect(containerPage.$(bitPublishingCss)).not.toHaveClass(publishedBit);
                    });

                    it("can remove staff only setting from published unit", function() {
                        promptSpy = edit_helpers.createPromptSpy();
                        renderContainerPage(this, mockContainerXBlockHtml, { published: true });
                        requestStaffOnly(true);
                        requestStaffOnly(false);
                        verifyStaffOnly(false);
                        expect(containerPage.$(bitPublishingCss)).toHaveClass(publishedBit);
                    });

                    it("does not refresh if removing staff only is canceled", function() {
                        var requestCount;
                        promptSpy = edit_helpers.createPromptSpy();
                        renderContainerPage(this, mockContainerXBlockHtml);
                        requestStaffOnly(true);
                        requestCount = requests.length;
                        containerPage.$('.action-staff-lock').click();
                        edit_helpers.confirmPrompt(promptSpy, true);    // Click 'No' to cancel
                        expect(requests.length).toBe(requestCount);
                        verifyStaffOnly(true);
                    });

                    it("does not refresh when failing to set staff only", function() {
                        var requestCount;
                        renderContainerPage(this, mockContainerXBlockHtml);
                        containerPage.$('.lock-checkbox').click();
                        requestCount = requests.length;
                        create_sinon.respondWithError(requests);
                        expect(requests.length).toBe(requestCount);
                        verifyStaffOnly(false);
                    });
                });
            });

            describe("PublishHistory", function () {
                var lastPublishCss = ".wrapper-last-publish";

                it('renders the last published date and user when the block is published', function() {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({
                        "published": true, "published_on": "Jul 01, 2014 at 12:45 UTC", "published_by": "amako"
                    });
                    expect(containerPage.$(lastPublishCss).text()).
                        toContain("Last published Jul 01, 2014 at 12:45 UTC by amako");
                });

                it('renders never published when the block is unpublished', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({ "published": false });
                    expect(containerPage.$(lastPublishCss).text()).toContain("Never published");
                });

                it('renders correctly when the block is published without publish info', function () {
                    renderContainerPage(this, mockContainerXBlockHtml);
                    fetch({
                        "published": true, "published_on": null, "published_by": null
                    });
                    expect(containerPage.$(lastPublishCss).text()).toContain("Previously published");
                });
            });

            describe("Message Area", function() {
                var messageSelector = '.container-message .warning',
                    warningMessage = 'This content is live for students. Edit with caution.';

                it('is empty for a unit that is not currently visible to students', function() {
                    renderContainerPage(this, mockContainerXBlockHtml, {
                        currently_visible_to_students: false
                    });
                    expect(containerPage.$(messageSelector).text().trim()).toBe('');
                });

                it('shows a message for a unit that is currently visible to students', function() {
                    renderContainerPage(this, mockContainerXBlockHtml, {
                        currently_visible_to_students: true
                    });
                    expect(containerPage.$(messageSelector).text().trim()).toBe(warningMessage);
                });

                it('hides the message when the unit is hidden from students', function() {
                    renderContainerPage(this, mockContainerXBlockHtml, {
                        currently_visible_to_students: true
                    });
                    fetch({ currently_visible_to_students: false });
                    expect(containerPage.$(messageSelector).text().trim()).toBe('');
                });

                it('shows a message when a unit is made visible', function() {
                    renderContainerPage(this, mockContainerXBlockHtml, {
                        currently_visible_to_students: false
                    });
                    fetch({ currently_visible_to_students: true });
                    expect(containerPage.$(messageSelector).text().trim()).toBe(warningMessage);
                });
            });
        });
    });
