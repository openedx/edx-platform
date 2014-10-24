var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.FormView = Backbone.View.extend({
        tagName: 'form',

        el: '',

        tpl: '',

        fieldTpl: '#form_field-tpl',

        events: {},

        errors: [],

        formType: '',

        $form: {},

        fields: [],

        // String to append to required label fields
        requiredStr: '*',

        initialize: function( data ) {
            this.tpl = $(this.tpl).html();
            this.fieldTpl = $(this.fieldTpl).html();

            this.buildForm( data.fields );
            this.model = data.model;

            this.listenTo( this.model, 'error', this.saveError );

            this.preRender( data );
        },

        /* Allows extended views to add custom
         * init steps without needing to repeat
         * default init steps
         */
        preRender: function( data ) {
            /* custom code goes here */
            return data;
        },

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
            this.$errors = $container.find('.submission-error');
        },

        buildForm: function( data ) {
            var html = [],
                i,
                len = data.length,
                fieldTpl = this.fieldTpl;

            this.fields = data;

            for ( i=0; i<len; i++ ) {
                html.push( _.template( fieldTpl, $.extend( data[i], {
                    form: this.formType,
                    requiredStr: this.requiredStr
                }) ) );
            }

            this.render( html.join('') );
        },

        /* Helper method ot toggle display
         * including accessibility considerations
         */
        element: {
            hide: function( $el ) {
                $el.addClass('hidden')
                   .attr('aria-hidden', true);
            },

            show: function( $el ) {
                $el.removeClass('hidden')
                   .attr('aria-hidden', false);
            }
        },

        forgotPassword: function( event ) {
            event.preventDefault();

            this.trigger('password-help');
        },

        getFormData: function() {

            var obj = {},
                $form = this.$form,
                elements = $form[0].elements,
                i,
                len = elements.length,
                $el,
                $label,
                key = '',
                errors = [],
                // $status = $form.find('.status'),
                test = {};

            for ( i=0; i<len; i++ ) {

                $el = $( elements[i] );
                $label = $form.find('label[for=' + $el.attr('id') + ']');
                key = $el.attr('name') || false;

                if ( key ) {
                    test = this.validate( elements[i], this.formType );

                    if ( test.isValid ) {
                        obj[key] = $el.attr('type') === 'checkbox' ? $el.is(':checked') : $el.val();
                        $el.removeClass('error');
                        $label.removeClass('error');
                    } else {
                        errors.push( test.message );
                        $el.addClass('error');
                        $label.addClass('error');
                    }
                }
            }

            this.errors = _.uniq( errors );

            return obj;
        },

        saveError: function( error ) {
            this.errors = ['<li>' + error.responseText + '</li>'];
            this.setErrors();
        },

        setErrors: function() {
            var $msg = this.$errors.find('.message-copy'),
                html = [],
                errors = this.errors,
                i,
                len = errors.length;

            for ( i=0; i<len; i++ ) {
                html.push( errors[i] );
            }

            $msg.html( html.join('') );

            this.element.show( this.$errors );
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

        toggleErrorMsg: function( show ) {
            if ( show ) {
                this.setErrors();
            } else {
                this.element.hide( this.$errors );
            }
        },
        validate: function( $el, form ) {
            return edx.utils.validate( $el, form );
        }
    });

})(jQuery, _, Backbone, gettext);
