/**
 * Provides helper methods for invoking Studio editors in Jasmine tests.
 */
define(["jquery", "js/spec_helpers/create_sinon", "js/views/modals/edit_xblock",
        "xmodule", "coffee/src/main", "xblock/cms.runtime.v1"],
    function($, create_sinon, EditXBlockModal) {

        var editorTemplate = readFixtures('metadata-editor.underscore'),
            numberEntryTemplate = readFixtures('metadata-number-entry.underscore'),
            stringEntryTemplate = readFixtures('metadata-string-entry.underscore'),
            feedbackTemplate = readFixtures('system-feedback.underscore'),
            editXBlockModalTemplate = readFixtures('edit-xblock-modal.underscore'),
            editorModeButtonTemplate = readFixtures('editor-mode-button.underscore'),
            installEditTemplates,
            showEditModal,
            isShowingModal,
            cancelModal;

        installEditTemplates = function() {
            setFixtures($("<script>", { id: "system-feedback-tpl", type: "text/template" }).text(feedbackTemplate));

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

        isShowingModal = function() {
            return $('.wrapper-modal-window').length > 0;
        };

        cancelModal = function(modal) {
            var modalElement, cancelButton;
            if (modal) {
                modalElement = modal.$el;
            } else {
                modalElement = $('.wrapper-modal-window');
            }
            cancelButton = modalElement.find('.action-cancel');
            expect(cancelButton.length).toBe(1);
            cancelButton.click();
        };

        return {
            'installEditTemplates': installEditTemplates,
            'showEditModal': showEditModal,
            'isShowingModal': isShowingModal,
            'cancelModal': cancelModal
        };
    });
