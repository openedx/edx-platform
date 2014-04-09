/**
 * Provides helper methods for invoking Studio editors in Jasmine tests.
 */
define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/modal_helpers", "js/views/modals/edit_xblock",
    "xmodule", "coffee/src/main", "xblock/cms.runtime.v1"],
    function($, create_sinon, modal_helpers, EditXBlockModal) {

        var editorTemplate = readFixtures('metadata-editor.underscore'),
            numberEntryTemplate = readFixtures('metadata-number-entry.underscore'),
            stringEntryTemplate = readFixtures('metadata-string-entry.underscore'),
            editXBlockModalTemplate = readFixtures('edit-xblock-modal.underscore'),
            editorModeButtonTemplate = readFixtures('editor-mode-button.underscore'),
            installMockXBlock,
            uninstallMockXBlock,
            hasSavedMockXBlock,
            installMockXModule,
            uninstallMockXModule,
            hasSavedMockXModule,
            installEditTemplates,
            showEditModal;

        installMockXBlock = function(mockResult) {
            window.MockXBlock = function(runtime, element) {
                return {
                    save: function() {
                        return mockResult;
                    }
                };
            };
        };

        uninstallMockXBlock = function() {
            window.MockXBlock = null;
        };

        installMockXModule = function(mockResult) {
            window.MockDescriptor = _.extend(XModule.Descriptor, {
                save: function() {
                    return mockResult;
                }
            });
        };

        uninstallMockXModule = function() {
            window.MockDescriptor = null;
        };

        installEditTemplates = function(append) {
            modal_helpers.installModalTemplates(append);

            // Add templates needed by the edit XBlock modal
            appendSetFixtures($("<script>", { id: "edit-xblock-modal-tpl", type: "text/template" }).text(editXBlockModalTemplate));
            appendSetFixtures($("<script>", { id: "editor-mode-button-tpl", type: "text/template" }).text(editorModeButtonTemplate));

            // Add templates needed by the settings editor
            appendSetFixtures($("<script>", {id: "metadata-editor-tpl", type: "text/template"}).text(editorTemplate));
            appendSetFixtures($("<script>", {id: "metadata-number-entry", type: "text/template"}).text(numberEntryTemplate));
            appendSetFixtures($("<script>", {id: "metadata-string-entry", type: "text/template"}).text(stringEntryTemplate));
        };

        showEditModal = function(requests, xblockElement, model, mockHtml) {
            var modal = new EditXBlockModal({});
            modal.edit(xblockElement, model);
            create_sinon.respondWithJson(requests, {
                html: mockHtml,
                "resources": []
            });
            return modal;
        };

        return $.extend(modal_helpers, {
            'installMockXBlock': installMockXBlock,
            'uninstallMockXBlock': uninstallMockXBlock,
            'installMockXModule': installMockXModule,
            'uninstallMockXModule': uninstallMockXModule,
            'installEditTemplates': installEditTemplates,
            'showEditModal': showEditModal
        });
    });
