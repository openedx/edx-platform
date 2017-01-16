
/* jshint strict: false */

var $el = $('#sticky'),
    stickyBarTop = $('#sticky').offset().top,
    MIN_WEB_WIDTH = 768;

$(document).ready(function() {
    'use strict';
    var makeSticky = function() {
        $el.css({
            position: 'fixed',
            top: 0,
            width: '100%',
            'z-index': '10',
            'box-shadow': '0px 1px 5px rgba(0,0,0,0.5)'
        });
        $('.sticky-course-title').removeClass('hidden');
        $('.course-run').addClass('hidden');
    };
    var removeSticky = function() {
        $el.css({
            position: 'static',
            'z-index': '0',
            'box-shadow': 'none'
        });
        $('.sticky-course-title').addClass('hidden');
        $('.course-run').removeClass('hidden');
    };
    var initializeSticky = function() {
        var windowTop = '';
        if ($el.length) {        // Element should exist
            $(window).scroll(function() {
                if ($(window).width() >= MIN_WEB_WIDTH) {
                    windowTop = $(window).scrollTop();
                    if (stickyBarTop < windowTop) {
                        makeSticky();
                    } else {
                        removeSticky();
                    }
                }
            });
        }
    };
    initializeSticky();
    $(window).resize(function() {
        if ($(window).width() >= MIN_WEB_WIDTH) {
            makeSticky();
        } else {
            removeSticky();
        }
    });
});
