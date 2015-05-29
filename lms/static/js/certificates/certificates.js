$(function () {
    $('.action-share-mozillaopenbadges').click(function (event) {
        $('.badges-overlay').fadeIn();
        event.preventDefault();
    })
    $('.badges-modal .close').click(function (event) {
        $('.badges-overlay').fadeOut();
    })
})