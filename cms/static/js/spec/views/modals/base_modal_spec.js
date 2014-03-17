define(["jquery", "underscore", "js/views/modals/base_modal"],
    function ($, _, BaseModal) {

        describe("BaseModal", function() {
            var baseViewPrototype, MockModal;

            MockModal = BaseModal.extend({
                initialize: function() {
                    this.viewHtml = readFixtures('mock/mock-modal.underscore');
                },

                render: function() {
                    this.$el.html(this.viewHtml);
                }
            });

            it('is visible after show is called', function () {
                var modal = new MockModal();
                modal.render();
                modal.show();
                expect($('body')).toHaveClass('modal-window-is-shown');
                expect(modal.$('.wrapper-modal-window')).toHaveClass('is-shown');
                modal.hide();
            });

            it('is invisible after hide is called', function () {
                var modal = new MockModal();
                modal.render();
                modal.show();
                modal.hide();
                expect($('body')).not.toHaveClass('modal-window-is-shown');
                expect(modal.$('.wrapper-modal-window')).not.toHaveClass('is-shown');
            });
        });
    });
