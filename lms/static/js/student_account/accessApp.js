var edx = edx || {};

(function($) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    return new edx.student.account.AccessView({
        mode: $('#login-and-registration-container').data('initial-mode') || 'login',
        thirdPartyAuth: $('#login-and-registration-container').data('third-party-auth-providers') || false
    });
})(jQuery);