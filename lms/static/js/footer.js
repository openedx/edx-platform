var edx = edx || {};

(function($) {
    'use strict';

    edx.footer = (function() {
        var _fn = {
            el: '#edx-branding-footer',

            init: function() {
                _fn.$el = $( _fn.el );

                /**
                 *  Only continue if the expected element
                 *  to add footer to is in the DOM
                 */
                if ( _fn.$el.length > 0 ) {
                    _fn.footer.get();
                }
            },

            analytics: {
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
                        showOpenEdXLogo = !!_fn.$el.data('show-openedx-logo'),
                        params = [];

                    if (showOpenEdXLogo) {
                        params.push('show-openedx-logo="1"');
                    }

                    if (language) {
                        params.push('language=' + language);
                    }

                    url += '/api/v1/branding/footer.html';

                    if (params) {
                        url += '?' + params.join('&');
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
                    _fn.analytics.eventListener();
                }
            }
        };

        return {
            load: _fn.init
        };
    })();

    edx.footer.load();
})(jQuery);
