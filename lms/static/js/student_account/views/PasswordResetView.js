define([
        'gettext',
        'jquery',
        'js/student_account/views/FormView',
        'text!js/student_account/templates/password_reset.underscore'
    ],
    function( gettext, $, FormView, passwordResetTpl ) {

        'use strict';

        return FormView.extend({
            el: '#password-reset-wrapper',

            tpl: passwordResetTpl,

            events: {
                'click .js-reset': 'submitForm'
            },

            formType: 'password-reset',

            requiredStr: '',

            submitButton: '.js-reset',

            preRender: function() {
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
                var $el = $(this.el),
                    $msg = $el.find('.js-reset-success');

                this.element.hide( $el.find('#password-reset-form') );
                this.element.show( $msg );
                this.element.scrollTop( $msg );
            }
        });

    }
);
