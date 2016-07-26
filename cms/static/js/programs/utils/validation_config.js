define([
        'backbone',
        'backbone.validation',
        'underscore',
        'gettext'
    ],
    function( Backbone, BackboneValidation, _, gettext ) {
        'use strict';

        var errorClass = 'has-error',
            messageEl = '.field-message',
            messageContent = '.field-message-content';

        // These are the same messages provided by Backbone.Validation,
        // marked for translation.
        // See: http://thedersen.com/projects/backbone-validation/#overriding-the-default-error-messages.
        _.extend( Backbone.Validation.messages, {
            required: gettext( '{0} is required' ),
            acceptance: gettext( '{0} must be accepted' ),
            min: gettext( '{0} must be greater than or equal to {1}' ),
            max: gettext( '{0} must be less than or equal to {1}' ),
            range: gettext( '{0} must be between {1} and {2}' ),
            length: gettext( '{0} must be {1} characters' ),
            minLength: gettext( '{0} must be at least {1} characters' ),
            maxLength: gettext( '{0} must be at most {1} characters' ),
            rangeLength: gettext( '{0} must be between {1} and {2} characters' ),
            oneOf: gettext( '{0} must be one of: {1}' ),
            equalTo: gettext( '{0} must be the same as {1}' ),
            digits: gettext( '{0} must only contain digits' ),
            number: gettext( '{0} must be a number' ),
            email: gettext( '{0} must be a valid email' ),
            url: gettext( '{0} must be a valid url' ),
            inlinePattern: gettext( '{0} is invalid' )
        });

        _.extend( Backbone.Validation.callbacks, {
            // Gets called when a previously invalid field in the
            // view becomes valid. Removes any error message.
            valid: function( view, attr, selector ) {
                var $input = view.$( '[' + selector + '~="' + attr + '"]' ),
                    $message = $input.siblings( messageEl );

                $input.removeClass( errorClass )
                      .removeAttr( 'data-error' );

                $message.removeClass( errorClass )
                        .find( messageContent )
                        .text( '' );
            },

            // Gets called when a field in the view becomes invalid.
            // Adds a error message.
            invalid: function( view, attr, error, selector ) {
                var $input = view.$( '[' + selector + '~="' + attr + '"]' ),
                    $message = $input.siblings( messageEl );

                $input.addClass( errorClass )
                      .attr( 'data-error', error );

                $message.addClass( errorClass )
                        .find( messageContent )
                        .text( $input.data('error') );
            }
        });

        Backbone.Validation.configure({
            labelFormatter: 'label'
        });
    }
);
