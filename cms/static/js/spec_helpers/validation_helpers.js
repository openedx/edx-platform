/**
 * Provides helper methods for invoking Validation modal in Jasmine tests.
 */
// eslint-disable-next-line no-undef
define(['jquery', 'js/spec_helpers/modal_helpers', 'common/js/spec_helpers/template_helpers'],
    function($, ModalHelpers, TemplateHelpers) {
        // eslint-disable-next-line no-var
        var installValidationTemplates, checkErrorContents, undoChanges;

        installValidationTemplates = function() {
            ModalHelpers.installModalTemplates();
            TemplateHelpers.installTemplate('validation-error-modal');
        };

        checkErrorContents = function(validationModal, errorObjects) {
            // eslint-disable-next-line no-var
            var errorItems = validationModal.$('.error-item-message');
            // eslint-disable-next-line no-var
            var i, item;
            /* eslint-disable-next-line camelcase, no-var */
            var num_items = errorItems.length;
            expect(num_items).toBe(errorObjects.length);

            // eslint-disable-next-line camelcase
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
