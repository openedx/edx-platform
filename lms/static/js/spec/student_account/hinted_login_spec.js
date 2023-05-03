(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'common/js/spec_helpers/template_helpers',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'js/student_account/views/HintedLoginView'
    ],
    function($, _, TemplateHelpers, AjaxHelpers, HintedLoginView) {
        describe('edx.student.account.HintedLoginView', function() {
            var view = null,
                requests = null,
                PLATFORM_NAME = 'edX',
                THIRD_PARTY_AUTH = {
                    currentProvider: null,
                    providers: [
                        {
                            id: 'oa2-google-oauth2',
                            name: 'Google',
                            iconClass: 'fa-google-plus',
                            loginUrl: '/auth/login/google-oauth2/?auth_entry=account_login',
                            registerUrl: '/auth/login/google-oauth2/?auth_entry=account_register'
                        },
                        {
                            id: 'oa2-facebook',
                            name: 'Facebook',
                            iconClass: 'fa-facebook',
                            loginUrl: '/auth/login/facebook/?auth_entry=account_login',
                            registerUrl: '/auth/login/facebook/?auth_entry=account_register'
                        }
                    ],
                    secondaryProviders: [
                        {
                            id: 'saml-harvard',
                            name: 'Harvard',
                            iconClass: 'fa-university',
                            loginUrl: '/auth/login/tpa-saml/?auth_entry=account_login&idp=harvard',
                            registerUrl: '/auth/login/tpa-saml/?auth_entry=account_register&idp=harvard'
                        }
                    ]
                };

            var createHintedLoginView = function(hintedProvider) {
                // Initialize the login view
                view = new HintedLoginView({
                    thirdPartyAuth: THIRD_PARTY_AUTH,
                    hintedProvider: hintedProvider,
                    platformName: PLATFORM_NAME
                });

                // Mock the redirect call
                spyOn(view, 'redirect').and.callFake(function() {});

                view.render();
            };

            beforeEach(function() {
                setFixtures('<div id="hinted-login-form"></div>');
                TemplateHelpers.installTemplate('templates/student_account/hinted_login');
            });

            it('displays a choice as two buttons', function() {
                createHintedLoginView('oa2-google-oauth2');

                expect($('.proceed-button.button-oa2-google-oauth2')).toBeVisible();
                expect($('.form-toggle')).toBeVisible();
                expect($('.proceed-button.button-oa2-facebook')).not.toBeVisible();
            });

            it('works with secondary providers as well', function() {
                createHintedLoginView('saml-harvard');

                expect($('.proceed-button.button-saml-harvard')).toBeVisible();
                expect($('.form-toggle')).toBeVisible();
                expect($('.proceed-button.button-oa2-google-oauth2')).not.toBeVisible();
            });

            it('redirects the user to the hinted provider if the user clicks the proceed button', function() {
                createHintedLoginView('oa2-google-oauth2');

                // Click the "Yes, proceed" button
                $('.proceed-button').click();

                expect(view.redirect).toHaveBeenCalledWith('/auth/login/google-oauth2/?auth_entry=account_login');
            });
        });
    });
}).call(this, define || RequireJS.define);
