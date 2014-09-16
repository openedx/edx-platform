/**
 * Provides helper methods for invoking Validation modal in Jasmine tests.
 */
define(['jquery', 'js/spec_helpers/modal_helpers', 'js/spec_helpers/view_helpers'],
    function($, modal_helpers, view_helpers) {
        var installValidationTemplates, checkErrorContents, undoChanges;

        installValidationTemplates = function () {
            modal_helpers.installModalTemplates();
            view_helpers.installTemplate('validation-error-modal');
        };

        checkErrorContents = function(validationModal, errorObjects) {
            var errorItems = validationModal.$('.error-item-message');
            var i, item;
            var num_items = errorItems.length;
            expect(num_items).toBe(errorObjects.length);

            for (i = 0; i < num_items; i++) {
                item = errorItems[i];
                expect(item.value).toBe(errorObjects[i].message);
            }
        };

        undoChanges = function(validationModal) {
            modal_helpers.pressModalButton('.action-undo', validationModal);
        };

        return $.extend(modal_helpers, {
            'installValidationTemplates': installValidationTemplates,
            'checkErrorContents': checkErrorContents,
            'undoChanges': undoChanges,
        });
    });