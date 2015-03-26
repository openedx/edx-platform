define(["js/spec_helpers/edit_helpers", "js/views/modals/base_modal", "xblock/cms.runtime.v1"],
    function (EditHelpers, BaseModal) {

        describe("Studio Runtime v1", function() {
            var runtime;

            beforeEach(function () {
                EditHelpers.installEditTemplates();
                runtime = new window.StudioRuntime.v1();
            });

            it('allows events to be listened to', function() {
                var canceled = false;
                runtime.listenTo('cancel', function() {
                    canceled = true;
                });
                expect(canceled).toBeFalsy();
                runtime.notify('cancel', {});
                expect(canceled).toBeTruthy();
            });

            it('shows save notifications', function() {
                var title = "Mock saving...",
                    notificationSpy = EditHelpers.createNotificationSpy();
                runtime.notify('save', {
                    state: 'start',
                    message: title
                });
                EditHelpers.verifyNotificationShowing(notificationSpy, title);
                runtime.notify('save', {
                    state: 'end'
                });
                EditHelpers.verifyNotificationHidden(notificationSpy);
            });

            it('shows error messages', function() {
                var title = "Mock Error",
                    message = "This is a mock error.",
                    notificationSpy = EditHelpers.createNotificationSpy("Error");
                runtime.notify('error', {
                    title: title,
                    message: message
                });
                EditHelpers.verifyNotificationShowing(notificationSpy, title);
            });

            describe("Modal Dialogs", function() {
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
                    EditHelpers.installEditTemplates();
                });

                afterEach(function() {
                    EditHelpers.hideModalIfShowing(modal);
                });

                it('cancels a modal dialog', function () {
                    showMockModal();
                    runtime.notify('modal-shown', modal);
                    expect(EditHelpers.isShowingModal(modal)).toBeTruthy();
                    runtime.notify('cancel');
                    expect(EditHelpers.isShowingModal(modal)).toBeFalsy();
                });
            });
        });
    });
