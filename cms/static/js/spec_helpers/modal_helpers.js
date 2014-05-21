/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(["jquery", "js/spec_helpers/view_helpers"],
    function($, view_helpers) {
        var installModalTemplates,
            getModalElement,
            isShowingModal,
            hideModalIfShowing,
            cancelModal,
            cancelModalIfShowing;

        installModalTemplates = function(append) {
            view_helpers.installViewTemplates(append);
            view_helpers.installTemplate('basic-modal');
            view_helpers.installTemplate('modal-button');
        };

        getModalElement = function(modal) {
            var modalElement;
            if (modal) {
                modalElement = modal.$('.wrapper-modal-window');
            } else {
                modalElement = $('.wrapper-modal-window');
            }
            return modalElement;
        };

        isShowingModal = function(modal) {
            var modalElement = getModalElement(modal);
            return modalElement.length > 0;
        };

        hideModalIfShowing = function(modal) {
            if (isShowingModal(modal)) {
                modal.hide();
            }
        };

        cancelModal = function(modal) {
            var modalElement, cancelButton;
            modalElement = getModalElement(modal);
            cancelButton = modalElement.find('.action-cancel:visible');
            expect(cancelButton.length).toBe(1);
            cancelButton.click();
        };

        cancelModalIfShowing = function(modal) {
            if (isShowingModal(modal)) {
                cancelModal(modal);
            }
        };

        return $.extend(view_helpers, {
            'installModalTemplates': installModalTemplates,
            'isShowingModal': isShowingModal,
            'hideModalIfShowing': hideModalIfShowing,
            'cancelModal': cancelModal,
            'cancelModalIfShowing': cancelModalIfShowing
        });
    });
