/**
 * MSA Account Migration Status enum
 */
(function(define) {
    'use strict';
    define(function() {
        return {
            EMAIL_LOOKUP: 'EMAIL_LOOKUP',
            LOGIN_NOT_MIGRATED: 'LOGIN_NOT_MIGRATED',
            LOGIN_MIGRATED: 'LOGIN_MIGRATED',
            REGISTER_NEW_USER: 'REGISTER_NEW_USER'
        };
    });
}).call(this, define || RequireJS.define);
