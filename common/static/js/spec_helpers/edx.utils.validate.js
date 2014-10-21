var edx = edx || {};

(function( $, _ ) {
    'use strict';

    edx.utils = edx.utils || {};

    var utils = (function(){
        var _fn = {
            validate: {

                field: function( el ) {
                    var $el = $(el);

                    return _fn.validate.required( $el ) &&
                           _fn.validate.charLength( $el ) &&
                           _fn.validate.email.valid( $el );
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

                required: function( $el ) {
                    if ($el.attr("type") === "checkbox") {
                        return $el.attr('required') ? $el.prop("checked") : true;
                    }
                    else {
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
                }
            }
        };

        return {
            validate: _fn.validate.field
        };

    })();

    edx.utils.validate = utils.validate;

})( jQuery, _ );