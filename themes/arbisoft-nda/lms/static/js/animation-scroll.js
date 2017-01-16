$(document).ready(function() {
    'use strict';

    var div = '';
    $('.back-to-top').on('click', function(event) {
        event.preventDefault();
        $('html, body').animate({scrollTop: 0}, 300);
    });

    $('ul.list-divided li.item a').on('click', function(event) {
        event.preventDefault();
        div = $(this).attr('href');
        $('html, body').animate({scrollTop: $(div).offset().top}, 300);
    });
});
