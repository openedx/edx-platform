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
                    var cookieValue = null,
                        cookies,
                        cookie = '',
                        i,
                        len;

                    if ( document.cookie && document.cookie !== '' ) {
                        cookies = document.cookie.split(';');
                        len = cookies.length;

                        for ( i = 0; i < len; i++ ) {
                            cookie = $.trim( cookies[i] );

                            // Does this cookie string begin with the name we want?
                            if ( cookie.substring( 0, name.length + 1 ) === ( name + '=' ) ) {
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                i = len;
                            }
                        }
                    }

                    return cookieValue;
                }
            },

            form: {
                submit: function( event ) {
                    var $email = $('#new-email'),
                        $password = $('#password'),
                        data = {
                            email: $email.val(),
                            password: $password.val()
                        };

                    event.preventDefault();

                    if ( _fn.form.validate( $email, $password, data ) ) {
                        _fn.ajax.put( 'email_change_request', data );
                    }
                },

                validate: function( $email, $password, data ) {
                    var valid = true;

                    // Clear errors
                    $email.removeClass('error');
                    $password.removeClass('error');

                    if ( !_fn.valid.email( data.email ) ) {
                        console.log('invalid email');
                        $email.addClass('error');
                        valid = false;
                    }

                    if ( !_fn.valid.password( data.password ) ) {
                        console.log('invalid password');
                        $password.addClass('error');
                        valid = false;
                    }

                    return valid;
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

                password: function( str ) {
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