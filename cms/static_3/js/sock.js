import * as domReady from 'domReady';
import * as $ from 'jquery';
import 'jquery.smoothScroll';

'use strict';

var toggleSock = function (e) {
    e.preventDefault();

    var $btnShowSockLabel = $(this).find('.copy-show');
    var $btnHideSockLabel = $(this).find('.copy-hide');
    var $sock = $('.wrapper-sock');
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

domReady(function () {
    // toggling footer additional support
    $('.cta-show-sock').bind('click', toggleSock);
});

export { toggleSock }
