// eslint-disable-next-line no-undef
define(['jquery'], function($) {
    var $body = $('body');
    var checkForCancel = function(e) {
        // eslint-disable-next-line eqeqeq
        if (e.which == 27) {
            $body.unbind('keyup', checkForCancel);
            e.data.$cancelButton.click();
        }
    };

    var cancelOnEscape = function(cancelButton) {
        $body.bind('keyup', {
            $cancelButton: cancelButton
        }, checkForCancel);
    };

    return cancelOnEscape;
});
