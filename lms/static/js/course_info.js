$(document).ready(function() {
    $('ul.tabs li').click(function() {
        $('ul.tabs li').removeClass('enabled');
        $(this).addClass('enabled');

        // eslint-disable-next-line camelcase
        var data_class = '.' + $(this).attr('data-class');

        $('.tab').slideUp();
        // eslint-disable-next-line camelcase
        $(data_class + ':hidden').slideDown();
    });
    var isSafari = !!navigator.userAgent.match(/Version\/[\d\.]+.*Safari/);
    if (isSafari) {
        $('.main-cta').addClass('safari-wrapper');
    }
});
