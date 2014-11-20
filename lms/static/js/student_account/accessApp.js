(function(require) {

    'use strict';

    require([
        'jquery',
        'js/student_account/views/AccessView'
    ],
    function( $, AccessView ) {

        return new AccessView({
            mode: $('#login-and-registration-container').data('initial-mode'),
            thirdPartyAuth: $('#login-and-registration-container').data('third-party-auth'),
            platformName: $('#login-and-registration-container').data('platform-name')
        });
    });
}(require));
