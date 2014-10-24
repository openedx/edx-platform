var edx = edx || {};

(function( $, _ ) {
    'use strict';

    edx.utils = edx.utils || {};

    var utils = (function(){
        var _fn = {
            validate: {

                msg: {
                    email: '<li>A properly formatted e-mail is required</li>',
                    min: '<li><%= field %> must be a minimum of <%= count %> characters long</li>',
                    max: '<li><%= field %> must be a maximum of <%= count %> characters long</li>',
                    required: '<li><%= field %> field is required</li>',
                    terms: '<li>To enroll you must agree to the <a href="#">Terms of Service and Honor Code</a></li>',
                    custom: '<li><%= content %></li>'
                },

                field: function( el ) {
                    var $el = $(el),
                        required = true,
                        min = true,
                        max = true,
                        email = true,
                        response = {},
                        isBlank = _fn.validate.isBlank( $el );

                    if ( _fn.validate.isRequired( $el ) ) {
console.log('is required');
                        if ( isBlank ) {
                            required = false;
                        } else {
                            min = _fn.validate.str.minlength( $el );
                            max = _fn.validate.str.maxlength( $el );
                            email = _fn.validate.email.valid( $el );
                        }
                    } else if ( !isBlank ) {
                        email = _fn.validate.email.valid( $el );
                    }

                    response.isValid = required && min && max && email;
console.log(response.isValid);
                    if ( !response.isValid ) {
                        response.message = _fn.validate.getMessage( $el, {
                            required: required,
                            min: min,
                            max: max,
                            email: email
                        });
                    }

                    return response;
                },

                str: {
                    minlength: function( $el ) {
                        var min = $el.attr('minlength') || 0;

                        return min <= $el.val().length;
                    },

                    maxlength: function( $el ) {
                        var max = $el.attr('maxlength') || false;

                        return ( !!max ) ? max >= $el.val().length : true;
                    },

                    capitalizeFirstLetter: function( str ) {
                        str = str.replace('_', ' ');

                        return str.charAt(0).toUpperCase() + str.slice(1);
                    }
                },

                isRequired: function( $el ) {
                    return $el.attr('required');
                },

                isBlank: function( $el ) {
                    return ( $el.attr('type') === 'checkbox' ) ? !$el.prop('checked') :  !$el.val();
                },

                email: {
                    // This is the same regex used to validate email addresses in Django 1.4
                    regex: new RegExp(
                        [
                            '(^[-!#$%&\'*+/=?^_`{}|~0-9A-Z]+(\\.[-!#$%&\'*+/=?^_`{}|~0-9A-Z]+)*',
                            '|^"([\\001-\\010\\013\\014\\016-\\037!#-\\[\\]-\\177]|\\\\[\\001-\\011\\013\\014\\016-\\177])*"',
                            ')@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[A-Z]{2,6}\\.?$)',
                            '|\\[(25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)(\\.(25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)){3}\\]$'
                        ].join(''), 'i'
                    ),

                    valid: function( $el ) {
                        return  $el.attr('type') === 'email' ? _fn.validate.email.format( $el.val() ) : true;
                    },

                    format: function( str ) {
                        return _fn.validate.email.regex.test( str );
                    }
                },

                getMessage: function( $el, tests ) {
                    var txt = [],
                        tpl,
                        name,
                        obj,
                        customMsg;

                    _.each( tests, function( value, key ) {
                        if ( !value ) {
                            name = $el.attr('name');
                            customMsg = $el.data('errormsg-' + key) || false;

                            // If the field has a custom error msg attached use it
                            if ( customMsg ) {
                                tpl = _fn.validate.msg.custom;

                                obj = {
                                    content: customMsg
                                };
                            } else {
                                tpl = _fn.validate.msg[key];

                                obj = {
                                    field: _fn.validate.str.capitalizeFirstLetter( name )
                                };

                                if ( key === 'min' ) {
                                    obj.count = $el.attr('minlength');
                                } else if ( key === 'max' ) {
                                    obj.count = $el.attr('maxlength');
                                }
                            }

                            txt.push( _.template( tpl, obj ) );
                        }
                    });

                    return txt.join(' ');
                }
            }
        };

        return {
            validate: _fn.validate.field
        };

    })();

    edx.utils.validate = utils.validate;

})( jQuery, _ );