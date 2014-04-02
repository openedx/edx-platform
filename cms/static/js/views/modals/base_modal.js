/**
 * This is a base modal implementation that provides common utilities.
 */
define(["jquery", "js/views/baseview"],
    function($, BaseView) {
        var BaseModal = BaseView.extend({
            options: $.extend({}, BaseView.prototype.options, {
                type: "prompt",
                closeIcon: false,
                icon: false
            }),

            show: function() {
                this.lastPosition = $(document).scrollTop();
                $('body').addClass('modal-window-is-shown');
                this.$('.wrapper-modal-window').addClass('is-shown');
            },

            hide: function() {
                $('body').removeClass('modal-window-is-shown');
                this.$('.wrapper-modal-window').removeClass('is-shown');
                $(document).scrollTop(this.lastPosition);
            }
        });

        return BaseModal;
    });
