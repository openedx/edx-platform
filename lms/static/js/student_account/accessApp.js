var edx = edx || {};

(function($) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    var container = $('#login-and-registration-container');

    return new edx.student.account.AccessView({
        mode: container.data('initial-mode'),
        thirdPartyAuth: container.data('third-party-auth'),
        thirdPartyAuthHint: container.data('third-party-auth-hint'),
        nextUrl: container.data('next-url'),
        platformName: container.data('platform-name'),
        loginFormDesc: container.data('login-form-desc'),
        registrationFormDesc: container.data('registration-form-desc'),
        passwordResetFormDesc: container.data('password-reset-form-desc')
    });
})(jQuery);
