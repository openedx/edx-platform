var edx = edx || {};

(function($) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    return new edx.student.account.AccessView({
        mode: $('#login-and-registration-container').data('initial-mode'),
        thirdPartyAuth: $('#login-and-registration-container').data('third-party-auth')
    });
})(jQuery);
