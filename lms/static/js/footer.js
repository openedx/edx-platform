var edx = edx || {};

(function($) {
    'use strict';

    edx.footer = (function() {
        var _fn = {
            el: '#edx-branding-footer',

            init: function() {
                _fn.$el = _fn.$el || $( _fn.el );

                /**
                 *  Only continue if the expected element
                 *  to add footer to is in the DOM
                 */
                if ( _fn.$el.length > 0 ) {
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
                    if ( _fn.$el.length > 0 ) {
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
                    var url = _fn.$el.data('base-url') || 'https://courses.edx.org',
                        language = _fn.$el.data('language') || false,
                        showOpenEdXLogo = Boolean(_fn.$el.data('show-openedx-logo')) || false,
                        params = [];

                    if (showOpenEdXLogo) {
                        params.push('show-openedx-logo="1"');
                    }

                    if (language) {
                        params.push('language="' + language + '"');
                    }

                    url = url + '/api/v1/branding/footer.html';

                    if (params) {
                        url = url + '?' + params.join('&');
                    }

                    $.ajax({
                        url: url,
                        type: 'GET',
                        dataType: 'html',
                        success: function( data ) {
                            _fn.footer.render( data );
                        }
                    });
                },

                render: function( html ) {
                    $(html).replaceAll(_fn.$el);
                }
            }
        };

        return {
            load: _fn.init,
            analytics: _fn.analytics.init
        };
    })();

    edx.footer.load();
    edx.footer.analytics();
})(jQuery);
