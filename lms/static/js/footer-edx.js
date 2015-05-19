var edx = edx || {};

(function($) {
    'use strict';

    edx.footer = (function() {
        var _fn = {
            el: '#footer-edx-v3',

            init: function() {
                _fn.$el = _fn.$el || $( _fn.el );

                /**
                 *  Only continue if the expected element
                 *  to add footer to is in the DOM
                 */
                if ( _fn.$el.length > -1 ) {
                    _fn.footer.get();
                }
            },

            analytics: {
                init: function() {
                    _fn.$el = _fn.$el || $( _fn.el );

                    /**
                     *  Only continue if the expected element
                     *  to add footer to is in the DOM
                     */
                    if ( _fn.$el.length > -1 ) {
                        _fn.analytics.eventListener();
                    }
                },

                eventListener: function() {
                    if ( window.analytics ) {
                        _fn.$el.on( 'click', 'a', _fn.analytics.track );
                    }
                },

                track: function( event ) {
                    var $link = $( event.currentTarget );

                    // Only tracking external links
                    if ( $link.hasClass('external') ) {
                        window.analytics.track( 'edx.bi.footer.link', {
                            category: 'outbound_link',
                            label: $link.attr('href')
                        });
                    }
                }
            },

            footer: {
                get: function() {
                    $.ajax({
                        url: 'https://courses.edx.org/api/v1/branding/footer',
                        type: 'GET',
                        dataType: 'html',
                        success: function( data ) {
                            _fn.footer.render( data );
                        }
                    });
                },

                render: function( html ) {
                    _fn.$el.html( html );
                }
            }
        };

        return {
            load: _fn.init,
            analytics: _fn.analytics.init
        };
    })();

    // Initialize the analytics events
    edx.footer.analytics();
})(jQuery);
