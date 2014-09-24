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
                },

                submit: function() {
                    $("#name-change-form").submit( _fn.form.submit );
                }
            },

            form: {
                submit: function( event ) {
                    var $newName = $('new-name');
                    var data = {
                        new_name: $newName.val()
                    };

                    event.preventDefault();
                    _fn.ajax.put( 'name_change', data );
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

        };

        return {
            init: _fn.init
        };

    })();

    edx.student.profile.init();

})(jQuery);