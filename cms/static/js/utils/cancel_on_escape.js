// eslint-disable-next-line no-undef
define(['jquery'], function($) {
    // eslint-disable-next-line no-var
    var $body = $('body');
    // eslint-disable-next-line no-var
    var checkForCancel = function(e) {
        // eslint-disable-next-line eqeqeq
        if (e.which == 27) {
            $body.unbind('keyup', checkForCancel);
            e.data.$cancelButton.click();
        }
    };

    // eslint-disable-next-line no-var
    var cancelOnEscape = function(cancelButton) {
        $body.bind('keyup', {
            $cancelButton: cancelButton
        }, checkForCancel);
    };

    return cancelOnEscape;
});
