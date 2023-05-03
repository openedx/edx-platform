(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'common/js/spec_helpers/template_helpers',
        'js/student_account/views/InstitutionLoginView'
    ],
    function($, _, TemplateHelpers, InstitutionLoginView) {
        describe('edx.student.account.InstitutionLoginView', function() {
            var view = null,
                PLATFORM_NAME = 'edX',
                THIRD_PARTY_AUTH = {
                    currentProvider: null,
                    providers: [],
                    secondaryProviders: [
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
                    ]
                };

            var createInstLoginView = function(mode) {
                // Initialize the login view
                view = new InstitutionLoginView({
                    mode: mode,
                    thirdPartyAuth: THIRD_PARTY_AUTH,
                    platformName: PLATFORM_NAME
                });
                view.render();
            };

            beforeEach(function() {
                setFixtures('<div id="institution_login-form"></div>');
                TemplateHelpers.installTemplate('templates/student_account/institution_login');
                TemplateHelpers.installTemplate('templates/student_account/institution_register');
            });

            it('displays a list of providers', function() {
                var $google, $facebook;

                createInstLoginView('login');
                expect($('#institution_login-form').html()).not.toBe('');
                $google = $('li a:contains("Google")');
                expect($google).toBeVisible();
                expect($google).toHaveAttr(
                    'href', '/auth/login/google-oauth2/?auth_entry=account_login'
                );
                $facebook = $('li a:contains("Facebook")');
                expect($facebook).toBeVisible();
                expect($facebook).toHaveAttr(
                    'href', '/auth/login/facebook/?auth_entry=account_login'
                );
            });

            it('displays a list of providers', function() {
                var $google, $facebook;

                createInstLoginView('register');
                expect($('#institution_login-form').html()).not.toBe('');
                $google = $('li a:contains("Google")');
                expect($google).toBeVisible();
                expect($google).toHaveAttr(
                    'href', '/auth/login/google-oauth2/?auth_entry=account_register'
                );
                $facebook = $('li a:contains("Facebook")');
                expect($facebook).toBeVisible();
                expect($facebook).toHaveAttr(
                    'href', '/auth/login/facebook/?auth_entry=account_register'
                );
            });
        });
    });
}).call(this, define || RequireJS.define);
