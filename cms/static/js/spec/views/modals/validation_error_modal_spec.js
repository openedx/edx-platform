define(['jquery', 'underscore', 'js/spec_helpers/validation_helpers', 'js/views/modals/validation_error_modal'],
    function ($, _, ValidationHelpers, ValidationErrorModal) {

        describe('ValidationErrorModal', function() {
            var modal, showModal;

            showModal = function (jsonContent, callback) {
                modal = new ValidationErrorModal();
                modal.setResetCallback(callback);
                modal.setContent(jsonContent);
                modal.show();
            };

            /* Before each, install templates required for the base modal
               and validation error modal. */
            beforeEach(function () {
                ValidationHelpers.installValidationTemplates();
            });

            afterEach(function() {
                ValidationHelpers.hideModalIfShowing(modal);
            });

            it('is visible after show is called', function () {
                showModal([]);
                expect(ValidationHelpers.isShowingModal(modal)).toBeTruthy();
            });

            it('displays none if no error given', function () {
                var errorObjects = [];

                showModal(errorObjects);
                expect(ValidationHelpers.isShowingModal(modal)).toBeTruthy();
                ValidationHelpers.checkErrorContents(modal, errorObjects);
            });

            it('correctly displays json error message objects', function () {
                var errorObjects = [
                    {
                        model: {display_name: 'test_attribute1'},
                        message: 'Encountered an error while saving test_attribute1'
                    },
                    {
                        model: {display_name: 'test_attribute2'},
                        message: 'Encountered an error while saving test_attribute2'
                    }
                ];

                showModal(errorObjects);
                expect(ValidationHelpers.isShowingModal(modal)).toBeTruthy();
                ValidationHelpers.checkErrorContents(modal, errorObjects);
            });

            it('run callback when undo changes button is clicked', function () {
                var errorObjects = [
                    {
                        model: {display_name: 'test_attribute1'},
                        message: 'Encountered an error while saving test_attribute1'
                    },
                    {
                        model: {display_name: 'test_attribute2'},
                        message: 'Encountered an error while saving test_attribute2'
                    }
                ];

                var callback = function() {
                    return true;
                };

                // Show Modal and click undo changes
                showModal(errorObjects, callback);
                expect(ValidationHelpers.isShowingModal(modal)).toBeTruthy();
                ValidationHelpers.undoChanges(modal);

                // Wait for the callback to be fired
                waitsFor(function () {
                    return callback();
                }, 'the callback to be called', 5000);

                // After checking callback fire, check modal hide
                runs(function () {
                    expect(ValidationHelpers.isShowingModal(modal)).toBe(false);
                });
            });
        });
    });
