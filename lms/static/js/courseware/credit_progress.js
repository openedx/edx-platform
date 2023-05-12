$(document).ready(function() {
    // eslint-disable-next-line no-var
    var $container = $('.requirement-container');
    // eslint-disable-next-line no-var
    var collapse = $container.data('eligible');
    // eslint-disable-next-line eqeqeq
    if (collapse == 'not_eligible') {
        $container.addClass('is-hidden');
        $('.detail-collapse').find('.fa').toggleClass('fa-caret-up fa-caret-down');
        $('.requirement-detail').text(gettext('More'));
    }
    $('.detail-collapse').on('click', function() {
        // eslint-disable-next-line no-var
        var $el = $(this);
        $container.toggleClass('is-hidden');
        $el.find('.fa').toggleClass('fa-caret-up fa-caret-down');
        $el.find('.requirement-detail').text(function(i, text) {
            return text === gettext('Less') ? gettext('More') : gettext('Less');
        });
    });
});
