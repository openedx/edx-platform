define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/edit_helpers",
    "js/views/pages/container", "js/models/xblock_info"],
    function ($, create_sinon, edit_helpers, ContainerPage, XBlockInfo) {

        describe("ContainerPage", function() {
            var model, containerPage, respondWithMockXBlockEditorFragment, mockContainerPage;

            mockContainerPage = readFixtures('mock/mock-container-page.underscore');

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

            respondWithMockXBlockEditorFragment = function(requests, response) {
                var requestIndex = requests.length - 1;
                create_sinon.respondWithJson(requests, response, requestIndex);
            };

            describe("Basic display", function() {
                var mockContainerXBlockHtml = readFixtures('mock/mock-container-xblock.underscore');

                it('can render itself', function() {
                    var requests = create_sinon.requests(this);
                    containerPage.render();
                    respondWithMockXBlockEditorFragment(requests, {
                        html: mockContainerXBlockHtml,
                        "resources": []
                    });

                    expect(containerPage.$el.select('.xblock-header')).toBeTruthy();
                    expect(containerPage.$('.wrapper-xblock')).not.toHaveClass('is-hidden');
                    expect(containerPage.$('.no-container-content')).toHaveClass('is-hidden');
                });

                it('shows a loading indicator', function() {
                    var requests = create_sinon.requests(this);
                    containerPage.render();
                    expect(containerPage.$('.ui-loading')).not.toHaveClass('is-hidden');
                    respondWithMockXBlockEditorFragment(requests, {
                        html: mockContainerXBlockHtml,
                        "resources": []
                    });
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
                    var requests = create_sinon.requests(this),
                        editButtons;
                    containerPage.render();
                    respondWithMockXBlockEditorFragment(requests, {
                        html: mockContainerXBlockHtml,
                        "resources": []
                    });
                    editButtons = containerPage.$('.edit-button');
                    // The container renders four mock xblocks, so there should be four edit buttons
                    expect(editButtons.length).toBe(4);
                    editButtons.first().click();
                    // Make sure that the correct xblock is requested to be edited
                    expect(requests[requests.length - 1].url).toBe(
                        '/xblock/testCourse/branch/draft/block/html447/studio_view'
                    );
                    create_sinon.respondWithJson(requests, {
                        html: mockXBlockEditorHtml,
                        "resources": []
                    });
                    expect(edit_helpers.isShowingModal()).toBeTruthy();
                });

                it('can save changes to settings', function() {
                    var requests, editButtons, modal, mockUpdatedXBlockHtml;
                    mockUpdatedXBlockHtml = readFixtures('mock/mock-updated-xblock.underscore');
                    requests = create_sinon.requests(this);
                    containerPage.render();
                    respondWithMockXBlockEditorFragment(requests, {
                        html: mockContainerXBlockHtml,
                        "resources": []
                    });
                    editButtons = containerPage.$('.edit-button');
                    // The container renders four mock xblocks, so there should be four edit buttons
                    expect(editButtons.length).toBe(4);
                    editButtons.first().click();
                    create_sinon.respondWithJson(requests, {
                        html: mockXBlockEditorHtml,
                        "resources": []
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
                    respondWithMockXBlockEditorFragment(requests, {
                        html: mockUpdatedXBlockHtml,
                        "resources": []
                    });
                    // Verify that the xblock was updated
                    expect(containerPage.$('.mock-updated-content').text()).toBe('Mock Update');
                    expect(edit_helpers.hasSavedMockXBlock()).toBe(true);
                });
            });

            describe("Empty container", function() {
                var mockContainerXBlockHtml = readFixtures('mock/mock-empty-container-xblock.underscore');

                it('shows the "no children" message', function() {
                    var requests = create_sinon.requests(this);
                    containerPage.render();
                    respondWithMockXBlockEditorFragment(requests, {
                        html: mockContainerXBlockHtml,
                        "resources": []
                    });

                    expect(containerPage.$('.no-container-content')).not.toHaveClass('is-hidden');
                    expect(containerPage.$('.wrapper-xblock')).toHaveClass('is-hidden');
                });
            });
        });
    });
