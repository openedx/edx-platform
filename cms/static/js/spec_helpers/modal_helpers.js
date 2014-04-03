/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery"],
    function($) {
        var basicModalTemplate = readFixtures('basic-modal.underscore'),
            modalButtonTemplate = readFixtures('modal-button.underscore'),
            feedbackTemplate = readFixtures('system-feedback.underscore'),
            installModalTemplates,
            isShowingModal,
            cancelModal;

        installModalTemplates = function(append) {
            if (append) {
                appendSetFixtures($("<script>", { id: "system-feedback-tpl", type: "text/template" }).text(feedbackTemplate));
            } else {
                setFixtures($("<script>", { id: "system-feedback-tpl", type: "text/template" }).text(feedbackTemplate));
            }
            appendSetFixtures($("<script>", { id: "basic-modal-tpl", type: "text/template" }).text(basicModalTemplate));
            appendSetFixtures($("<script>", { id: "modal-button-tpl", type: "text/template" }).text(modalButtonTemplate));
        };

        isShowingModal = function(modal) {
            var modalElement;
            if (modal) {
                modalElement = modal.$('.wrapper-modal-window');
            } else {
                modalElement = $('.wrapper-modal-window');
            }
            return modalElement.length > 0;
        };

        cancelModal = function(modal) {
            var modalElement, cancelButton;
            if (modal) {
                modalElement = modal.$('.wrapper-modal-window');
            } else {
                modalElement = $('.wrapper-modal-window');
            }
            cancelButton = modalElement.find('.action-cancel');
            expect(cancelButton.length).toBe(1);
            cancelButton.click();
        };

        return {
            'installModalTemplates': installModalTemplates,
            'isShowingModal': isShowingModal,
            'cancelModal': cancelModal
        };
    });
