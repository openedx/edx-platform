var edx = edx || {};

(function($) {
    'use strict';

    edx.student = edx.student || {};

    edx.student.account = (function() {
        var _fn = {
            init: function() {
                _fn.ajax.init();
                _fn.eventHandlers.init();
            },

            eventHandlers: {
                init: function() {
                    _fn.eventHandlers.submit();
                },

                submit: function() {
                    $('#email-change-form').submit( _fn.form.submit );
                }
            },

            ajax: {
                init: function() {
                    var csrftoken = _fn.cookie.get( 'csrftoken' );

                    $.ajaxSetup({
                        beforeSend: function(xhr, settings) {
                            if ( settings.type === 'PUT' ) {
                                xhr.setRequestHeader( 'X-CSRFToken', csrftoken );
                            }
                        }
                    });
                },

                put: function( url, data ) {
                    $.ajax({
                        url: url,
                        type: 'PUT',
                        data: data
                    });
                }
            },

            cookie: {
                get: function( name ) {
                    return $.cookie(name);
                }
            },

            form: {
                isValid: true,

                submit: function( event ) {
                    var $email = $('#new-email'),
                        $password = $('#password'),
                        data = {
                            new_email: $email.val(),
                            password: $password.val()
                        };

                    event.preventDefault();

                    _fn.form.validate( $('#email-change-form') );

                    if ( _fn.form.isValid ) {
                        _fn.ajax.put( 'email_change_request', data );
                    }
                },

                validate: function( $form ) {
                    _fn.form.isValid = true;
                    $form.find('input').each( _fn.valid.input );
                }
            },

            regex: {
                email: function() {
                    // taken from http://parsleyjs.org/
                    return /^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))$/i;
                }
            },

            valid: {
                email: function( str ) {
                    var valid = false,
                        len = str ? str.length : 0,
                        regex = _fn.regex.email();

                    if ( 0 < len && len < 254 ) {
                        valid = regex.test( str );
                    }

                    return valid;
                },

                input: function() {
                    var $el = $(this),
                        validation = $el.data('validate'),
                        value = $el.val(),
                        valid = true;


                    if ( validation && validation.length > 0 ) {
                        $el.removeClass('error')
                            .css('border-color', '#c8c8c8'); // temp. for development

                        // Required field
                        if ( validation.indexOf('required') > -1 ) {
                            valid = _fn.valid.required( value );
                        }

                        // Email address
                        if ( valid && validation.indexOf('email') > -1 ) {
                            valid = _fn.valid.email( value );
                        }

                        if ( !valid ) {
                            $el.addClass('error')
                                .css('border-color', '#f00'); // temp. for development
                            _fn.form.isValid = false;
                        }
                    }
                },

                required: function( str ) {
                    return ( str && str.length > 0 ) ? true : false;
                }
            }
        };

        return {
            init: _fn.init
        };
    })();

    edx.student.account.init();

})(jQuery);