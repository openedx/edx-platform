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
    // eslint-disable-next-line no-useless-escape
    var isSafari = !!navigator.userAgent.match(/Version\/[\d\.]+.*Safari/);
    if (isSafari) {
        $('.main-cta').addClass('safari-wrapper');
    }
});
