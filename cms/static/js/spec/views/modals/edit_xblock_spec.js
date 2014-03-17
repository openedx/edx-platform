define(["jquery", "underscore", "js/spec_helpers/create_sinon", "js/spec_helpers/edit_helpers",
        "js/views/modals/edit_xblock", "js/models/xblock_info"],
    function ($, _, create_sinon, edit_helpers, EditXBlockModal, XBlockInfo) {

        describe("EditXBlockModal", function() {
            var model, modal, showModal;

            showModal = function(requests, mockHtml) {
                var xblockElement = $('.xblock');
                return edit_helpers.showEditModal(requests, xblockElement, model, mockHtml);
            };

            beforeEach(function () {
                edit_helpers.installEditTemplates();
                appendSetFixtures('<div class="xblock" data-locator="mock-xblock" data-display-name="Mock XBlock"></div>');
                model = new XBlockInfo({
                    id: 'testCourse/branch/published/block/verticalFFF',
                    display_name: 'Test Unit',
                    category: 'vertical'
                });
            });

            describe("Editing an xblock", function() {
                var mockXBlockEditorHtml;

                mockXBlockEditorHtml = readFixtures('mock/mock-xblock-editor.underscore');

                beforeEach(function () {
                    window.MockXBlock = function(runtime, element) {
                        return { };
                    };
                });

                afterEach(function() {
                    window.MockXBlock = null;
                });

                it('can show itself', function() {
                    var requests = create_sinon.requests(this);
                    modal = showModal(requests, mockXBlockEditorHtml);
                    expect(modal.$('.wrapper-modal-window')).toHaveClass('is-shown');
                    edit_helpers.cancelModal(modal);
                    expect(modal.$('.wrapper-modal-window')).not.toHaveClass('is-shown');
                });

                it('does not show any editor mode buttons', function() {
                    var requests = create_sinon.requests(this);
                    modal = showModal(requests, mockXBlockEditorHtml);
                    expect(modal.$('.editor-modes a').length).toBe(0);
                    edit_helpers.cancelModal(modal);
                });
            });

            describe("Editing an xmodule", function() {
                var mockXModuleEditorHtml;

                mockXModuleEditorHtml = readFixtures('mock/mock-xmodule-editor.underscore');

                beforeEach(function() {
                    // Mock the VerticalDescriptor so that the module can be rendered
                    window.VerticalDescriptor = XModule.Descriptor;
                });

                afterEach(function () {
                    window.VerticalDescriptor = null;
                });

                it('can render itself', function() {
                    var requests = create_sinon.requests(this);

                    // Show the modal using a mock xblock response
                    modal = showModal(requests, mockXModuleEditorHtml);
                    expect(modal.$('.wrapper-modal-window')).toHaveClass('is-shown');
                    edit_helpers.cancelModal(modal);
                    expect(modal.$('.wrapper-modal-window')).not.toHaveClass('is-shown');
                });

                it('shows the correct default buttons', function() {
                    var requests = create_sinon.requests(this),
                        editorButton,
                        settingsButton;
                    modal = showModal(requests, mockXModuleEditorHtml);
                    expect(modal.$('.editor-modes a').length).toBe(2);
                    editorButton = modal.$('.editor-button');
                    settingsButton = modal.$('.settings-button');
                    expect(editorButton.length).toBe(1);
                    expect(editorButton).toHaveClass('is-set');
                    expect(settingsButton.length).toBe(1);
                    expect(settingsButton).not.toHaveClass('is-set');
                    edit_helpers.cancelModal(modal);
                });
            });
        });
    });
