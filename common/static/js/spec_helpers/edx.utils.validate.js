var edx = edx || {};

(function( $, _ ) {
    'use strict';

    edx.utils = edx.utils || {};

    var utils = (function(){
        var _fn = {
            validate: {

                msg: {
                    email: '<p>A properly formatted e-mail is required</p>',
                    min: '<p><%= field %> must be a minimum of <%= length %> characters long',
                    max: '<p><%= field %> must be a maximum of <%= length %> characters long',
                    password: '<p>A valid password is required</p>',
                    required: '<p><%= field %> field is required</p>',
                    terms: '<p>To enroll you must agree to the <a href="#">Terms of Service and Honor Code</a></p>'
                },

                field: function( el ) {
                    var $el = $(el),
                        required = _fn.validate.required( $el ),
                        // length = _fn.validate.charLength( $el ),
                        min = _fn.validate.str.minlength( $el ),
                        max = _fn.validate.str.maxlength( $el ),
                        email = _fn.validate.email.valid( $el ),
                        response = {
                            isValid: required && min && max && email
                        };

                    if ( !response.isValid ) {
                        response.message = _fn.validate.getMessage( $el, {
                            required: required,
                            // length: length,
                            min: min,
                            max: max,
                            email: email
                        });
                    }

                    return response;
                },

                charLength: function( $el ) {
                    var type = $el.attr("type");
                    if (type !== "text" && type !== "textarea" && type !== "password") {
                        return true;
                    }

                    // Cannot assume there will be both min and max
                    var min = $el.attr('minlength') || 0,
                        max = $el.attr('maxlength') || false,
                        chars = $el.val().length,
                        within = false;

                    // if max && min && within the range
                    if ( min <= chars && ( max && chars <= max ) ) {
                        within = true;
                    } else if ( min <= chars && !max ) {
                        within = true;
                    }

                    return within;
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

                required: function( $el ) {
                    if ( $el.attr('type') === 'checkbox' ) {
                        return $el.attr('required') ? $el.prop('checked') : true;
                    } else {
                        return $el.attr('required') ? $el.val() : true;
                    }
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
                        return  $el.data('email') ? _fn.validate.email.format( $el.val() ) : true;
                    },

                    format: function( str ) {
                        return _fn.validate.email.regex.test( str );
                    }
                },

                getMessage: function( $el, tests ) {
                    var txt = [],
                        tpl,
                        name;

                    _.each( tests, function( value, key ) {
                        if ( !value ) {
                            name = $el.attr('name');

                            tpl = _fn.validate.msg[key];

                            txt.push( _.template( tpl, {
                                field: _fn.validate.str.capitalizeFirstLetter( name )
                            }));
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