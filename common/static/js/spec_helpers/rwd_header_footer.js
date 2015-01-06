/**
 * Adds rwd classes and click handlers.
 */

(function($) {
    'use strict';

    var rwd = (function() {

        var _fn = {
            header: 'header.global-new',

            footer: '.edx-footer-new',

            resultsUrl: 'course-search',

            init: function() {
                _fn.$header = $( _fn.header );
                _fn.$footer = $( _fn.footer );
                _fn.$nav = _fn.$header.find('nav');
                _fn.$globalNav = _fn.$nav.find('.nav-global');

                _fn.add.elements();
                _fn.add.classes();
                _fn.eventHandlers.init();
            },

            add: {
                classes: function() {
                    // Add any RWD-specific classes
                    _fn.$header.addClass('rwd');
                    _fn.$footer.addClass('rwd');
                },

                elements: function() {
                    _fn.add.burger();
                    _fn.add.registerLink();
                },

                burger: function() {
                    _fn.$nav.prepend([
                        '<a href="#" class="mobile-menu-button" aria-label="menu">',
                            '<i class="icon fa fa-reorder" aria-hidden="true"></i>',
                        '</a>'
                    ].join(''));
                },

                registerLink: function() {
                    var $register = _fn.$nav.find('.cta-register'),
                        $li = {},
                        $a = {},
                        count = 0;

                    // Add if register link is shown
                    if ( $register.length > 0 ) {
                        count = _fn.$globalNav.find('li').length + 1;

                        // Create new li
                        $li = $('<li/>');
                        $li.addClass('desktop-hide nav-global-0' + count);

                        // Clone register link and remove classes
                        $a = $register.clone();
                        $a.removeClass();

                        // append to DOM
                        $a.appendTo( $li );
                        _fn.$globalNav.append( $li );
                    }
                }
            },

            eventHandlers: {
                init: function() {
                    _fn.eventHandlers.click();
                },

                click: function() {
                    // Toggle menu
                    _fn.$nav.on( 'click', '.mobile-menu-button', _fn.toggleMenu );
                }
            },

            toggleMenu: function( event ) {
                event.preventDefault();

                _fn.$globalNav.toggleClass('show');
            }
        };

        return {
            init: _fn.init
        };
    })();

    setTimeout( function() {
        rwd.init();
    }, 100);
})(jQuery);
