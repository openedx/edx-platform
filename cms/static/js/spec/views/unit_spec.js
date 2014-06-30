define(["jquery", "underscore.string", "jasmine", "coffee/src/views/unit", "js/models/module_info",
    "js/spec_helpers/create_sinon", "js/spec_helpers/edit_helpers", "jasmine-stealth"],
    function ($, str, jasmine, UnitEditView, ModuleModel, create_sinon, edit_helpers) {
        var requests, unitView, initialize, lastRequest, respondWithHtml, verifyComponents, i,
            mockXBlockEditorHtml = readFixtures('mock/mock-xblock-editor.underscore');

        respondWithHtml = function(html, requestIndex) {
            create_sinon.respondWithJson(
                requests,
                { html: html, "resources": [] },
                requestIndex
            );
        };

        initialize = function(test) {
            var mockXBlockHtml = readFixtures('mock/mock-unit-page-xblock.underscore'),
                mockChildContainerHtml = readFixtures('mock/mock-unit-page-child-container.underscore'),
                model;
            requests = create_sinon.requests(test);
            model = new ModuleModel({
                id: 'unit_locator',
                state: 'draft'
            });
            unitView = new UnitEditView({
                el: $('.main-wrapper'),
                templates: edit_helpers.mockComponentTemplates,
                model: model
            });

            // Respond with renderings for the two xblocks in the unit (the second is itself a child container)
            respondWithHtml(mockXBlockHtml, 0);
            respondWithHtml(mockChildContainerHtml, 1);
        };

        lastRequest = function() { return requests[requests.length - 1]; };

        verifyComponents = function (unit, locators) {
            var components = unit.$(".component");
            expect(components.length).toBe(locators.length);
            for (i = 0; i < locators.length; i++) {
                expect($(components[i]).data('locator')).toBe(locators[i]);
            }
        };

        beforeEach(function() {
            edit_helpers.installMockXBlock();

            // needed to stub out the ajax
            window.analytics = jasmine.createSpyObj('analytics', ['track']);
            window.course_location_analytics = jasmine.createSpy('course_location_analytics');
            window.unit_location_analytics = jasmine.createSpy('unit_location_analytics');
        });

        afterEach(function () {
            edit_helpers.uninstallMockXBlock();
        });

        describe("UnitEditView", function() {
            beforeEach(function() {
                edit_helpers.installEditTemplates();
                appendSetFixtures(readFixtures('mock/mock-unit-page.underscore'));
            });

            describe('duplicateComponent', function() {
                var clickDuplicate;

                clickDuplicate = function (index) {
                    unitView.$(".duplicate-button")[index].click();
                };

                it('sends the correct JSON to the server', function () {
                    initialize(this);
                    clickDuplicate(0);
                    edit_helpers.verifyXBlockRequest(requests, {
                        "duplicate_source_locator": "loc_1",
                        "parent_locator": "unit_locator"
                    });
                });

                it('inserts duplicated component immediately after source upon success', function () {
                    initialize(this);
                    clickDuplicate(0);
                    create_sinon.respondWithJson(requests, {"locator": "duplicated_item"});
                    verifyComponents(unitView, ['loc_1', 'duplicated_item', 'loc_2']);
                });

                it('inserts duplicated component at end if source at end', function () {
                    initialize(this);
                    clickDuplicate(1);
                    create_sinon.respondWithJson(requests, {"locator": "duplicated_item"});
                    verifyComponents(unitView, ['loc_1', 'loc_2', 'duplicated_item']);
                });

                it('shows a notification while duplicating', function () {
                    var notificationSpy = edit_helpers.createNotificationSpy();
                    initialize(this);
                    clickDuplicate(0);
                    edit_helpers.verifyNotificationShowing(notificationSpy, /Duplicating/);
                    create_sinon.respondWithJson(requests, {"locator": "new_item"});
                    edit_helpers.verifyNotificationHidden(notificationSpy);
                });

                it('does not insert duplicated component upon failure', function () {
                    initialize(this);
                    clickDuplicate(0);
                    create_sinon.respondWithError(requests);
                    verifyComponents(unitView, ['loc_1', 'loc_2']);
                });
            });

            describe('createNewComponent ', function () {
                var clickNewComponent;

                clickNewComponent = function () {
                    unitView.$(".new-component .new-component-type a.single-template").click();
                };

                it('sends the correct JSON to the server', function () {
                    initialize(this);
                    clickNewComponent();
                    edit_helpers.verifyXBlockRequest(requests, {
                        "category": "discussion",
                        "type": "discussion",
                        "parent_locator": "unit_locator"
                    });
                });

                it('inserts new component at end', function () {
                    initialize(this);
                    clickNewComponent();
                    create_sinon.respondWithJson(requests, {"locator": "new_item"});
                    verifyComponents(unitView, ['loc_1', 'loc_2', 'new_item']);
                });

                it('shows a notification while creating', function () {
                    var notificationSpy = edit_helpers.createNotificationSpy();
                    initialize(this);
                    clickNewComponent();
                    edit_helpers.verifyNotificationShowing(notificationSpy, /Adding/);
                    create_sinon.respondWithJson(requests, {"locator": "new_item"});
                    edit_helpers.verifyNotificationHidden(notificationSpy);
                });

                it('does not insert new component upon failure', function () {
                    initialize(this);
                    clickNewComponent();
                    create_sinon.respondWithError(requests);
                    verifyComponents(unitView, ['loc_1', 'loc_2']);
                });
            });

            describe("Disabled edit/publish links during ajax call", function() {
                var link,
                    draft_states = [
                        {
                            state: "draft",
                            selector: ".publish-draft"
                        },
                        {
                            state: "public",
                            selector: ".create-draft"
                        }
                    ];

                function test_link_disabled_during_ajax_call(draft_state) {
                    it("re-enables the " + draft_state.selector + " link once the ajax call returns", function() {
                        initialize(this);
                        link = $(draft_state.selector);
                        expect(link).not.toHaveClass('is-disabled');
                        link.click();
                        expect(link).toHaveClass('is-disabled');
                        create_sinon.respondWithError(requests);
                        expect(link).not.toHaveClass('is-disabled');
                    });
                }

                for (i = 0; i < draft_states.length; i++) {
                    test_link_disabled_during_ajax_call(draft_states[i]);
                }
            });

            describe("Editing an xblock", function() {
                var newDisplayName = 'New Display Name';

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

                it('can show an edit modal for a child xblock', function() {
                    var editButtons;
                    initialize(this);
                    editButtons = unitView.$('.edit-button');
                    // The container renders two mock xblocks
                    expect(editButtons.length).toBe(2);
                    editButtons[1].click();
                    // Make sure that the correct xblock is requested to be edited
                    expect(str.startsWith(lastRequest().url, '/xblock/loc_2/studio_view')).toBeTruthy();
                    create_sinon.respondWithJson(requests, {
                        html: mockXBlockEditorHtml,
                        resources: []
                    });

                    // Expect that a modal is shown with the correct title
                    expect(edit_helpers.isShowingModal()).toBeTruthy();
                    expect(edit_helpers.getModalTitle()).toBe('Editing: Test Child Container');

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
                    initialize(this);
                    editButtons = unitView.$('.edit-button');
                    // The container renders two mock xblocks
                    expect(editButtons.length).toBe(2);
                    editButtons[1].click();
                    create_sinon.respondWithJson(requests, {
                        html: mockXModuleEditor,
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
                        id: 'mock-id'
                    });

                    // Respond to the request to refresh
                    respondWithHtml(mockUpdatedXBlockHtml);

                    // Verify that the xblock was updated
                    expect(unitView.$('.mock-updated-content').text()).toBe('Mock Update');
                });
            });

        });
    });
