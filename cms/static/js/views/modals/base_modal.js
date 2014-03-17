/**
 * This is a base modal implementation that provides common utilities.
 */
define(["jquery", "underscore", "underscore.string", "gettext", "js/views/baseview"],
    function($, _, str, gettext, BaseView) {
        var BaseModal = BaseView.extend({
            options: $.extend({}, BaseView.prototype.options, {
                type: "prompt",
                closeIcon: false,
                icon: false
            }),

            show: function() {
                $('body').addClass('modal-window-is-shown');
                this.$('.wrapper-modal-window').addClass('is-shown');
            },

            hide: function() {
                $('body').removeClass('modal-window-is-shown');
                this.$('.wrapper-modal-window').removeClass('is-shown');
            }
        });

        return BaseModal;
    });
