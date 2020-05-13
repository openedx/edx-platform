(function(define) {
    'use strict';

    define([
        'jquery',
        'logger'
    ],
        function($, Logger) {
            return function() {
                // This function performs all actions common to all courseware.
                // 1. adding an event to all link clicks.
                $('a:not([href^="#"])').click(function(event) {
                    Logger.log(
                        'edx.ui.lms.link_clicked',
                        {
                            current_url: window.location.href,
                            target_url: event.currentTarget.href
                        });
                });
            };
        }
    );
}).call(this, define || RequireJS.define);

$(document).ready(function() {
    'use strict';

    $('.toggle-links-dropdown, .toggle-links-dropdown span').click(function(e) {
        var $dropdownMenu = $('.nav-item .dropdown-links-menu');
        var $userDropdown = $('.toggle-links-dropdown');
        if ($dropdownMenu.is(':visible')) {
            $dropdownMenu.addClass('hidden');
            $userDropdown.attr('aria-expanded', 'false');
        } else {
            $dropdownMenu.removeClass('hidden');
            $dropdownMenu.find('.dropdown-item')[0].focus();
            $userDropdown.attr('aria-expanded', 'true');
        }
        $('.toggle-links-dropdown').toggleClass('open');
        e.stopPropagation();
    });
    // Hide links dropdown on click away
    if ($('.nav-item .dropdown-links-menu').length) {
        $(window).click(function(e) {
            var $dropdownMenu = $('.nav-item .dropdown-links-menu');
            var $userDropdown = $('.toggle-links-dropdown');
            if ($userDropdown.is(':visible') && !$(e.target).is('.dropdown-item, .toggle-links-dropdown')) {
                $dropdownMenu.addClass('hidden');
                $userDropdown.attr('aria-expanded', 'false');
            }
        });
    }
});
