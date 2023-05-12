import * as domReady from 'domReady';
import * as $ from 'jquery';
import 'jquery.smoothScroll';

// eslint-disable-next-line no-unused-expressions
'use strict';

/* eslint-disable-next-line import/no-mutable-exports, no-var */
var toggleSock = function(e) {
    e.preventDefault();

    // eslint-disable-next-line no-var
    var $btnShowSockLabel = $(this).find('.copy-show');
    // eslint-disable-next-line no-var
    var $btnHideSockLabel = $(this).find('.copy-hide');
    // eslint-disable-next-line no-var
    var $sock = $('.wrapper-sock');
    // eslint-disable-next-line no-var
    var $sockContent = $sock.find('.wrapper-inner');

    if ($sock.hasClass('is-shown')) {
        $sock.removeClass('is-shown');
        $sockContent.hide('fast');
        $btnHideSockLabel.removeClass('is-shown').addClass('is-hidden');
        $btnShowSockLabel.removeClass('is-hidden').addClass('is-shown');
    } else {
        $sock.addClass('is-shown');
        $sockContent.show('fast');
        $btnHideSockLabel.removeClass('is-hidden').addClass('is-shown');
        $btnShowSockLabel.removeClass('is-shown').addClass('is-hidden');
    }

    $.smoothScroll({
        offset: -200,
        easing: 'swing',
        speed: 1000,
        scrollElement: null,
        scrollTarget: $sock
    });
};

domReady(function() {
    // toggling footer additional support
    $('.cta-show-sock').bind('click', toggleSock);
});

// eslint-disable-next-line import/prefer-default-export
export {toggleSock};
