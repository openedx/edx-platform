;(function (define) {
    'use strict';
    define([
            'jquery',
            'underscore',
            'backbone',
            'common/js/utils/edx.utils.validate'
        ],
        function($, _, Backbone, EdxUtilsValidate) {

        return Backbone.View.extend({
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

            submitButton: '',

            initialize: function( data ) {
                this.model = data.model;
                this.preRender( data );

                this.tpl = $(this.tpl).html();
                this.fieldTpl = $(this.fieldTpl).html();
                this.buildForm( data.fields );

                this.listenTo( this.model, 'error', this.saveError );
            },

            /* Allows extended views to add custom
             * init steps without needing to repeat
             * default init steps
             */
            preRender: function( data ) {
                /* Custom code goes here */
                return data;
            },

            render: function( html ) {
                var fields = html || '';

                $(this.el).html( _.template(this.tpl)({
                    fields: fields
                }));

                this.postRender();

                return this;
            },

            postRender: function() {
                var $container = $(this.el);
                this.$form = $container.find('form');
                this.$errors = $container.find('.submission-error');
                this.$submitButton = $container.find(this.submitButton);
            },

            buildForm: function( data ) {
                var html = [],
                    i,
                    len = data.length,
                    fieldTpl = this.fieldTpl;

                this.fields = data;

                for ( i=0; i<len; i++ ) {
                    if ( data[i].errorMessages ) {
                        data[i].errorMessages = this.escapeStrings( data[i].errorMessages );
                    }

                    html.push( _.template(fieldTpl)($.extend( data[i], {
                        form: this.formType,
                        requiredStr: this.requiredStr
                    }) ) );
                }

                this.render( html.join('') );
            },

            /* Helper method to toggle display
             * including accessibility considerations
             */
            element: {
                hide: function( $el ) {
                    if ( $el ) {
                        $el.addClass('hidden');
                    }
                },

                scrollTop: function( $el ) {
                    // Scroll to top of selected element
                    $('html,body').animate({
                        scrollTop: $el.offset().top
                    },'slow');
                },

                show: function( $el ) {
                    if ( $el ) {
                        $el.removeClass('hidden');
                    }
                }
            },

            escapeStrings: function( obj ) {
                _.each( obj, function( val, key ) {
                    obj[key] = _.escape( val );
                });

                return obj;
            },

            focusFirstError: function() {
                var $error = this.$form.find('.error').first(),
                    $field = {},
                    $parent = {};

                if ( $error.is('label') ) {
                    $parent = $error.parent('.form-field');
                    $error = $parent.find('input') || $parent.find('select');
                } else {
                    $field = $error;
                }

                $error.focus();
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
                    test = {};

                for ( i=0; i<len; i++ ) {

                    $el = $( elements[i] );
                    $label = $form.find('label[for=' + $el.attr('id') + ']');
                    key = $el.attr('name') || false;

                    if ( key ) {
                        test = this.validate( elements[i] );
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
                this.toggleDisableButton(false);
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

                // Scroll to error messages
                $('html,body').animate({
                    scrollTop: this.$errors.offset().top
                },'slow');

                // Focus on first error field
                this.focusFirstError();
            },

            /* Allows extended views to add non-form attributes
             * to the data before saving it to model 
             */
            setExtraData: function( data ) {
                return data;
            },

            submitForm: function( event ) {
                var data = this.getFormData();

                if (!_.isUndefined(event)) {
                    event.preventDefault();
                }

                this.toggleDisableButton(true);

                if ( !_.compact(this.errors).length ) {
                    data = this.setExtraData( data );
                    this.model.set( data );
                    this.model.save();
                    this.toggleErrorMsg( false );
                } else {
                    this.toggleErrorMsg( true );
                }

                this.postFormSubmission();
            },

            /* Allows extended views to add custom
             * code after form submission
             */
            postFormSubmission: function() {
                return true;
            },

            toggleErrorMsg: function( show ) {
                if ( show ) {
                    this.setErrors();
                    this.toggleDisableButton(false);
                } else {
                    this.element.hide( this.$errors );
                }
            },

            /**
             * If a form button is defined for this form, this will disable the button on
             * submit, and re-enable the button if an error occurs.
             *
             * Args:
             *      disabled (boolean): If set to TRUE, disable the button.
             *
             */
            toggleDisableButton: function ( disabled ) {
                if (this.$submitButton) {
                    this.$submitButton.attr('disabled', disabled);
                }
            },

            validate: function( $el ) {
                return EdxUtilsValidate.validate( $el );
            }
        });
    });
}).call(this, define || RequireJS.define);
