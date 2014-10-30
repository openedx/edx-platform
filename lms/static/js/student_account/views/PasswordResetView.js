var edx = edx || {};

(function($, _, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.PasswordResetView = edx.student.account.FormView.extend({
        el: '#password-reset-wrapper',

        tpl: '#password_reset-tpl',

        events: {
            'click .js-reset': 'submitForm'
        },

        formType: 'password-reset',

        requiredStr: '',

        postRender: function() {
            var $container = $(this.el);

            this.$form = $container.find('form');

            this.$errors = $container.find('.submission-error');

            this.listenTo( this.model, 'success', this.resetComplete );
            this.listenTo( this.model, 'error', this.saveError );
        },

        toggleErrorMsg: function( show ) {
            if ( show ) {
                this.setErrors();
            } else {
                this.element.hide( this.$errors );
            }
        },

        resetComplete: function() {
            var $el = $(this.el);

            this.element.hide( $el.find('#password-reset-form') );
            this.element.show( $el.find('.js-reset-success') );
        }
    });

})(jQuery, _, gettext);
