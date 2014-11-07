var edx = edx || {};

(function($, gettext) {
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

        preRender: function( data ) {
            this.listenTo( this.model, 'sync', this.saveSuccess );
        },

        toggleErrorMsg: function( show ) {
            if ( show ) {
                this.setErrors();
            } else {
                this.element.hide( this.$errors );
            }
        },

        saveSuccess: function() {
            var $el = $(this.el);

            this.element.hide( $el.find('#password-reset-form') );
            this.element.show( $el.find('.js-reset-success') );
        }
    });

})(jQuery, gettext);
