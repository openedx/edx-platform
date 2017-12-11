/**
 * Provides helper methods for invoking Validation modal in Jasmine tests.
 */
define(['jquery', 'js/spec_helpers/modal_helpers', 'common/js/spec_helpers/template_helpers'],
    function($, ModalHelpers, TemplateHelpers) {
        var installValidationTemplates, checkErrorContents, undoChanges;

        installValidationTemplates = function() {
            ModalHelpers.installModalTemplates();
            TemplateHelpers.installTemplate('validation-error-modal');
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
            ModalHelpers.pressModalButton('.action-undo', validationModal);
        };

        return $.extend(ModalHelpers, {
            installValidationTemplates: installValidationTemplates,
            checkErrorContents: checkErrorContents,
            undoChanges: undoChanges
        });
    });
