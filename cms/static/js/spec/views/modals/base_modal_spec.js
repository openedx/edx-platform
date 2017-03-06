define(["jquery", "underscore", "js/views/modals/base_modal", "js/spec_helpers/modal_helpers"],
    function ($, _, BaseModal, ModelHelpers) {

        describe("BaseModal", function() {
            var MockModal, modal, showMockModal;

            MockModal = BaseModal.extend({
                getContentHtml: function() {
                    return readFixtures('mock/mock-modal.underscore');
                }
            });

            showMockModal = function() {
                modal = new MockModal({
                    title: "Mock Modal"
                });
                modal.show();
            };

            beforeEach(function () {
                ModelHelpers.installModalTemplates();
            });

            afterEach(function() {
                ModelHelpers.hideModalIfShowing(modal);
            });

            describe("Single Modal", function() {
                it('is visible after show is called', function () {
                    showMockModal();
                    expect(ModelHelpers.isShowingModal(modal)).toBeTruthy();
                });

                it('sends focus to the modal window after show is called', function(done) {
                    showMockModal();

                    jasmine.waitUntil(function() {
                        var modalWindow = ModelHelpers.getModalWindow(modal);
                        return ($(modalWindow)[0] === $(modalWindow)[0].ownerDocument.activeElement);
                    }).then(done);
                });

                it('is removed after hide is called', function () {
                    showMockModal();
                    modal.hide();
                    expect(ModelHelpers.isShowingModal(modal)).toBeFalsy();
                });

                it('is removed after cancel is clicked', function () {
                    showMockModal();
                    ModelHelpers.cancelModal(modal);
                    expect(ModelHelpers.isShowingModal(modal)).toBeFalsy();
                });
            });

            describe("Nested Modal", function() {
                var nestedModal, showNestedModal;

                showNestedModal = function() {
                    showMockModal();
                    nestedModal = new MockModal({
                        title: "Nested Modal",
                        parent: modal
                    });
                    nestedModal.show();
                };

                afterEach(function() {
                    if (nestedModal && ModelHelpers.isShowingModal(nestedModal)) {
                        nestedModal.hide();
                    }
                });

                it('is visible after show is called', function () {
                    showNestedModal();
                    expect(ModelHelpers.isShowingModal(nestedModal)).toBeTruthy();
                });

                it('is removed after hide is called', function () {
                    showNestedModal();
                    nestedModal.hide();
                    expect(ModelHelpers.isShowingModal(nestedModal)).toBeFalsy();

                    // Verify that the parent modal is still showing
                    expect(ModelHelpers.isShowingModal(modal)).toBeTruthy();
                });

                it('is removed after cancel is clicked', function () {
                    showNestedModal();
                    ModelHelpers.cancelModal(nestedModal);
                    expect(ModelHelpers.isShowingModal(nestedModal)).toBeFalsy();

                    // Verify that the parent modal is still showing
                    expect(ModelHelpers.isShowingModal(modal)).toBeTruthy();
                });
            });
        });
    });
