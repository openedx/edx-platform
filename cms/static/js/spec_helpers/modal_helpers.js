/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
// eslint-disable-next-line no-undef
define(['jquery', 'common/js/spec_helpers/template_helpers', 'common/js/spec_helpers/view_helpers'],
    function($, TemplateHelpers, ViewHelpers) {
        // eslint-disable-next-line no-var
        var installModalTemplates, getModalElement, getModalWindow, getModalTitle, isShowingModal,
            hideModalIfShowing, pressModalButton, cancelModal, cancelModalIfShowing;

        installModalTemplates = function(append) {
            ViewHelpers.installViewTemplates(append);
            TemplateHelpers.installTemplate('basic-modal');
            TemplateHelpers.installTemplate('modal-button');
        };

        getModalElement = function(modal) {
            // eslint-disable-next-line no-var
            var $modalElement;
            if (modal) {
                $modalElement = modal.$('.wrapper-modal-window');
            } else {
                $modalElement = $('.wrapper-modal-window');
            }
            return $modalElement;
        };

        getModalWindow = function(modal) {
            // eslint-disable-next-line no-var
            var modalElement = getModalElement(modal);
            return modalElement.find('.modal-window');
        };

        getModalTitle = function(modal) {
            // eslint-disable-next-line no-var
            var modalElement = getModalElement(modal);
            return modalElement.find('.modal-window-title').text();
        };

        isShowingModal = function(modal) {
            // eslint-disable-next-line no-var
            var modalElement = getModalElement(modal);
            return modalElement.length > 0;
        };

        hideModalIfShowing = function(modal) {
            if (isShowingModal(modal)) {
                modal.hide();
            }
        };

        pressModalButton = function(selector, modal) {
            // eslint-disable-next-line no-var
            var modalElement, button;
            modalElement = getModalElement(modal);
            button = modalElement.find(selector + ':visible');
            expect(button.length).toBe(1);
            button.click();
        };

        cancelModal = function(modal) {
            pressModalButton('.action-cancel', modal);
        };

        cancelModalIfShowing = function(modal) {
            if (isShowingModal(modal)) {
                cancelModal(modal);
            }
        };

        return $.extend(ViewHelpers, {
            getModalElement: getModalElement,
            getModalWindow: getModalWindow,
            getModalTitle: getModalTitle,
            installModalTemplates: installModalTemplates,
            isShowingModal: isShowingModal,
            hideModalIfShowing: hideModalIfShowing,
            pressModalButton: pressModalButton,
            cancelModal: cancelModal,
            cancelModalIfShowing: cancelModalIfShowing
        });
    });
