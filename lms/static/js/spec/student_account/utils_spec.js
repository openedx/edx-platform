define(['jquery', 'js/student_account/utils'],
    function($, Utils) {
        'use strict';
        describe('edxUserCookie', function() {
            var userInfo, user;

            userInfo = {
                version: 1,
                username: 'local-test-user'
            };

            beforeEach(function() {
                document.cookie = 'edx-user-info="' +
                  '{\"version\": 1, \"username\": \"local-test-user\"}";'; // eslint-disable-line no-useless-escape
            });

            it('returns correct user information from cookie', function() {
                spyOn(Utils, 'getHostname').and.returnValue('localhost');

                user = Utils.userFromEdxUserCookie();
                expect(user).toEqual(userInfo);
            });
        });
    }
);
