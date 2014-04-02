define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/edit_helpers",
    "js/views/xblock_container", "js/models/xblock_info"],
    function ($, create_sinon, edit_helpers, XBlockContainerView, XBlockInfo) {

        describe("XBlockContainerView", function() {
            var model, containerView, respondWithMockXBlockEditorFragment, mockContainerView;

            mockContainerView = readFixtures('mock/mock-container-view.underscore');

            beforeEach(function () {
                edit_helpers.installEditTemplates();
                appendSetFixtures(mockContainerView);

                model = new XBlockInfo({
                    id: 'testCourse/branch/published/block/verticalFFF',
                    display_name: 'Test Unit',
                    category: 'vertical'
                });
                containerView = new XBlockContainerView({
                    model: model,
                    el: $('#content')
                });
            });

            respondWithMockXBlockEditorFragment = function(requests, response) {
                var requestIndex = requests.length - 1;
                create_sinon.respondWithJson(requests, response, requestIndex);
            };

            describe("Editing an xblock", function() {
                var mockContainerXBlockHtml,
                    mockXBlockEditorHtml;


                beforeEach(function () {
                    window.MockXBlock = function(runtime, element) {
                        return { };
                    };
                });

                afterEach(function() {
                    window.MockXBlock = null;
                    if (edit_helpers.isShowingModal()) {
                        edit_helpers.cancelModal();
                    }
                });

                mockContainerXBlockHtml = readFixtures('mock/mock-container-xblock.underscore');
                mockXBlockEditorHtml = readFixtures('mock/mock-xblock-editor.underscore');

                it('can render itself', function() {
                    var requests = create_sinon.requests(this);
                    containerView.render();
                    respondWithMockXBlockEditorFragment(requests, {
                        html: mockContainerXBlockHtml,
                        "resources": []
                    });

                    expect(containerView.$el.select('.xblock-header')).toBeTruthy();
                });


                it('can show an edit modal for a child xblock', function() {
                    var requests = create_sinon.requests(this),
                        editButtons;
                    containerView.render();
                    respondWithMockXBlockEditorFragment(requests, {
                        html: mockContainerXBlockHtml,
                        "resources": []
                    });
                    editButtons = containerView.$('.edit-button');
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
                    expect($('.wrapper-modal-window')).toHaveClass('is-shown');
                });
            });
        });
    });
