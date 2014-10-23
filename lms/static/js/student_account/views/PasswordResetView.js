var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.PasswordResetView = edx.student.account.FormView.extend({
        el: '#password-reset-wrapper',

        tpl: '#password_reset-tpl',

        events: {
            'click .js-reset': 'submitForm'
        },

        requiredStr: '',

        postRender: function() {
            var $container = $(this.el);

            this.$form = $container.find('form');

            this.$resetFail = $container.find('.js-reset-fail');
            this.$errors = $container.find('.submission-error');

            this.listenTo( this.model, 'success', this.resetComplete );
            this.listenTo( this.model, 'error', this.resetError );
        },

        toggleErrorMsg: function( show ) {
            if ( show ) {
                this.setErrors();
            } else {
                this.$errors
                    .addClass('hidden')
                    .attr('aria-hidden', true);
            }
        },

        resetComplete: function() {
            var $el = $(this.el);

            $el.find('#password-reset-form').addClass('hidden');
            $el.find('.js-reset-success').removeClass('hidden');

            this.$resetFail.addClass('hidden');
        },

        resetError: function() {
            this.$resetFail.removeClass('hidden');
        },

        submitForm: function( event ) {
            var data = this.getFormData();

            event.preventDefault();

            if ( !_.compact(this.errors).length ) {
                this.model.set( data );
                this.model.save();
                this.toggleErrorMsg( false );
            } else {
                this.toggleErrorMsg( true );
            }
        },

        validate: function( $el ) {
            return edx.utils.validate( $el );
        }
    });

})(jQuery, _, Backbone, gettext);
