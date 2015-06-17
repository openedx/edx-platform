var edx = edx || {};

(function($, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.PasswordResetView = edx.student.account.FormView.extend({
        el: '#password-reset-form',

        tpl: '#password_reset-tpl',

        events: {
            'click .js-reset': 'submitForm'
        },

        formType: 'password-reset',

        requiredStr: '',

        submitButton: '.js-reset',

        preRender: function() {
            this.element.show( $( this.el ) );
            this.element.show( $( this.el ).parent() );
            this.listenTo( this.model, 'sync', this.saveSuccess );
        },

        toggleErrorMsg: function( show ) {
            if ( show ) {
                this.setErrors();
                this.toggleDisableButton(false);
            } else {
                this.element.hide( this.$errors );
            }
        },

        saveSuccess: function() {
            this.trigger('password-email-sent');

            // Destroy the view (but not el) and unbind events
            this.$el.empty().off();
            this.stopListening();
        }
    });

})(jQuery, gettext);
