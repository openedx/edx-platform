define(["jquery"], function($) {
    var $body = $('body');
    var checkForCancel = function (e) {
        if (e.which == 27) {
            $body.unbind('keyup', checkForCancel);
            e.data.$cancelButton.click();
        }
    };

    var bindCheckForCancel = function (cancelButton) {
        $body.bind('keyup', {
            $cancelButton: cancelButton
        }, checkForCancel);
    };

    return bindCheckForCancel;
});