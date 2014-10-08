var edx = edx || {};

(function($) {
    'use strict';

    edx.student = edx.student || {};

    edx.student.profile = (function() {

        var _fn = {
            init: function() {
                _fn.ajax.init();
                _fn.eventHandlers.init();
            },

            eventHandlers: {
                init: function() {
                    _fn.eventHandlers.submit();
                    _fn.eventHandlers.click();
                },

                submit: function() {
                    $('#name-change-form').on( 'submit', _fn.update.name );
                },

                click: function() {
                    $('#language-change-form .submit-button').on( 'click', _fn.update.language );
                }
            },

            update: {
                name: function( event ) {
                    _fn.form.submit( event, '#new-name', 'new_name', 'name_change' );
                },

                language: function( event ) {
                    /** 
                     * The onSuccess argument here means: take `window.location.reload`
                     * and return a function that will use `window.location` as the 
                     * `this` reference inside `reload()`.
                     */
                    _fn.form.submit( event, '#new-language', 'new_language', 'language_change', window.location.reload.bind(window.location) );
                }
            },

            form: {
                submit: function( event, idSelector, key, url, onSuccess ) {
                    var $selection = $(idSelector),
                        data = {};

                    data[key] = $selection.val();

                    event.preventDefault();
                    _fn.ajax.put( url, data, onSuccess );
                }
            },

            ajax: {
                init: function() {
                    var csrftoken = _fn.cookie.get( 'csrftoken' );

                    $.ajaxSetup({
                        beforeSend: function( xhr, settings ) {
                            if ( settings.type === 'PUT' ) {
                                xhr.setRequestHeader( 'X-CSRFToken', csrftoken );
                            }
                        }
                    });
                },

                put: function( url, data, onSuccess ) {
                    $.ajax({
                        url: url,
                        type: 'PUT',
                        data: data,
                        success: onSuccess ? onSuccess : ''
                    });
                }
            },

            cookie: {
                get: function( name ) {
                    return $.cookie(name);
                }
            },

        };

        return {
            init: _fn.init
        };

    })();

    edx.student.profile.init();

})(jQuery);
