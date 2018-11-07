$(document).ready(function() {
    var $container = $('.requirement-container');
    var collapse = $container.data('eligible');
    if (collapse == 'not_eligible') {
        $container.addClass('is-hidden');
        $('.detail-collapse').find('.fa').toggleClass('fa-caret-up fa-caret-down');
        $('.requirement-detail').text(gettext('More'));
    }
    $('.detail-collapse').on('click', function() {
        var $el = $(this);
        $container.toggleClass('is-hidden');
        $el.find('.fa').toggleClass('fa-caret-up fa-caret-down');
        $el.find('.requirement-detail').text(function(i, text) {
            return text === gettext('Less') ? gettext('More') : gettext('Less');
        });
    });
});
