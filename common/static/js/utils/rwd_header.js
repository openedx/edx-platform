/**
 * Adds rwd classes and click handlers.
 */

(function($) {
    'use strict';

    var rwd = (function() {

        var _fn = {
            header: 'header.global-new',

            resultsUrl: 'course-search',

            init: function() {
                _fn.$header = $( _fn.header );
                _fn.$footer = $( _fn.footer );
                _fn.$navContainer = _fn.$header.find('.nav-container');
                _fn.$globalNav = _fn.$header.find('.nav-global');

                _fn.add.elements();
                _fn.add.classes();
                _fn.eventHandlers.init();
            },

            add: {
                classes: function() {
                    // Add any RWD-specific classes
                    _fn.$header.addClass('rwd');
                },

                elements: function() {
                    _fn.add.burger();
                    _fn.add.registerLink();
                },

                burger: function() {
                    _fn.$navContainer.prepend([
                        '<a href="#" class="mobile-menu-button" aria-label="menu">',
                            '<i class="icon fa fa-bars" aria-hidden="true"></i>',
                        '</a>'
                    ].join(''));
                },

                registerLink: function() {
                    var $register = _fn.$header.find('.cta-register'),
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
                    _fn.$header.on( 'click', '.mobile-menu-button', _fn.toggleMenu );
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

    rwd.init();
})(jQuery);
