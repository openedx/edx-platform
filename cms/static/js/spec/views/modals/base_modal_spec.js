define(["jquery", "underscore", "js/views/modals/base_modal", "js/spec_helpers/modal_helpers"],
    function ($, _, BaseModal, modal_helpers) {

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
                modal_helpers.installModalTemplates();
            });

            afterEach(function() {
                if (modal && modal_helpers.isShowingModal(modal)) {
                    modal.hide();
                }
            });

            describe("Single Modal", function() {
                it('is visible after show is called', function () {
                    showMockModal();
                    expect(modal_helpers.isShowingModal(modal)).toBeTruthy();
                });

                it('is removed after hide is called', function () {
                    showMockModal();
                    modal.hide();
                    expect(modal_helpers.isShowingModal(modal)).toBeFalsy();
                });

                it('is removed after cancel is clicked', function () {
                    showMockModal();
                    modal_helpers.cancelModal(modal);
                    expect(modal_helpers.isShowingModal(modal)).toBeFalsy();
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
                    if (nestedModal && modal_helpers.isShowingModal(nestedModal)) {
                        nestedModal.hide();
                    }
                });

                it('is visible after show is called', function () {
                    showNestedModal();
                    expect(modal_helpers.isShowingModal(nestedModal)).toBeTruthy();
                });

                it('is removed after hide is called', function () {
                    showNestedModal();
                    nestedModal.hide();
                    expect(modal_helpers.isShowingModal(nestedModal)).toBeFalsy();

                    // Verify that the parent modal is still showing
                    expect(modal_helpers.isShowingModal(modal)).toBeTruthy();
                });

                it('is removed after cancel is clicked', function () {
                    showNestedModal();
                    modal_helpers.cancelModal(nestedModal);
                    expect(modal_helpers.isShowingModal(nestedModal)).toBeFalsy();

                    // Verify that the parent modal is still showing
                    expect(modal_helpers.isShowingModal(modal)).toBeTruthy();
                });
            });
        });
    });
