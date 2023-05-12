$(function() {
    if ($('.filter nav').length > 0) {
        // eslint-disable-next-line no-var
        var offset = $('.filter nav').offset().top;

        // eslint-disable-next-line consistent-return
        $(window).scroll(function() {
            if (offset <= window.pageYOffset) {
                return $('.filter nav').addClass('fixed-top');
            } else if (offset >= window.pageYOffset) {
                return $('.filter nav').removeClass('fixed-top');
            }
        });
    }
});
