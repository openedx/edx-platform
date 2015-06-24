$(document).ready(function() {
    $('.detail-collapse').on('click', function() {
        var el = $(this);
        $('.requirement-container').toggleClass('is-hidden');
        el.find('.fa').toggleClass('fa-caret-down fa-caret-up');
        el.find('.requirement-detail').text(function(i, text){
          return text === gettext('More') ? gettext('Less') : gettext('More');
        });
    });

});
