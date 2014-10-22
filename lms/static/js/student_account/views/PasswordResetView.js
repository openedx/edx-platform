var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.PasswordResetView = Backbone.View.extend({
        tagName: 'form',

        el: '#password-reset-wrapper',

        tpl: '#password_reset-tpl',

        fieldTpl: '#form_field-tpl',

        events: {
            'click .js-reset': 'submitForm'
        },

        errors: [],

        mode: {},

        $form: {},

        initialize: function() {
            this.fieldTpl = $(this.fieldTpl).html();

            var fields = this.buildForm([{
                name: 'email',
                label: 'Email',
                defaultValue: '',
                type: 'text',
                required: true,
                placeholder: 'xsy@edx.org',
                instructions: 'This is the email address you used to register with edX.',
                restrictions: {}
            }]);

            this.tpl = $(this.tpl).html();
            this.initModel();
            this.render( fields );
        },

        // Renders the form.
        render: function( html ) {
            var fields = html || '';

            $(this.el).html( _.template( this.tpl, {
                fields: fields
            }));

            this.postRender();

            return this;
        },

        postRender: function() {
            var $container = $(this.el);

            this.$form = $container.find('form');
            this.$errors = $container.find('.error-msg');
            this.$resetFail = $container.find('.js-reset-fail');

            this.listenTo( this.model, 'success', this.resetComplete );
            this.listenTo( this.model, 'error', this.resetError );
        },

        initModel: function() {
            this.model = new edx.student.account.PasswordResetModel();
        },

        buildForm: function( data ) {
            var html = [],
                i,
                len = data.length,
                fieldTpl = this.fieldTpl;

            for ( i=0; i<len; i++ ) {
                html.push( _.template( fieldTpl, $.extend( data[i], {
                    form: 'reset-password'
                }) ) );
            }

            return html.join('');
        },

        getFormData: function() {
            var obj = {},
                $form = this.$form,
                elements = $form[0].elements,
                i,
                len = elements.length,
                $el,
                key = '',
                errors = [];

            for ( i=0; i<len; i++ ) {

                $el = $( elements[i] );
                key = $el.attr('name') || false;

                if ( key ) {
                    if ( this.validate( elements[i] ) ) {
                        obj[key] = $el.attr('type') === 'checkbox' ? $el.is(':checked') : $el.val();
                        $el.css('border', '1px solid #ccc');
                    } else {
                        errors.push( key );
                        $el.css('border', '2px solid red');
                    }
                }
            }

            this.errors = errors;

            return obj;
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

            if ( !this.errors.length ) {
                this.model.set( data );
                this.model.save();
                this.toggleErrorMsg( false );
            } else {
                this.toggleErrorMsg( true );
            }
        },

        toggleErrorMsg: function( show ) {
            if ( show ) {
                this.$errors.removeClass('hidden');
            } else {
                this.$errors.addClass('hidden');
            }
        },

        validate: function( $el ) {
            return edx.utils.validate( $el );
        }
    });

})(jQuery, _, Backbone, gettext);
