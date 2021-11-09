define(['jquery', 'js/student_account/utils'],
    function($, Utils) {
        'use strict';
        describe('edxUserCookie', function() {
            var user,
                edxUserInfoCookieName = 'edx-user-info', 
                userInfo = {
                    version: 1,
                    username: 'local-test-user'
                };

            beforeEach(function() {
                document.cookie = edxUserInfoCookieName + '="' +
                  '{\"version\": 1, \"username\": \"local-test-user\"}";'; // eslint-disable-line no-useless-escape
            });

            it('returns correct user information from cookie', function() {
                user = Utils.userFromEdxUserCookie(edxUserInfoCookieName);
                expect(user).toEqual(userInfo);
            });
        });
    }
);
