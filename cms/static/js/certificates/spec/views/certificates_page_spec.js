// Jasmine Test Suite: Certifiate Page View

define([
    'jquery', 'underscore', 'js/certificates/views/certificates_page',
    'js/certificates/models/certificate', 'js/certificates/collections/certificates',
    'js/common_helpers/template_helpers'
], function ($, _, CertificatesPage, CertificateModel, CertificateCollection, TemplateHelpers) {
    'use strict';
    describe('CertificatesPage', function() {
        var mockCertificatesPage = readFixtures(
                'mock/mock-certificate-page.underscore'
            ),
            certificateItemClassName = '.certificates-list-item';

        var initializePage = function (disableSpy) {
            var view = new CertificatesPage({
                el: $('#content'),
                certificatesEnabled: true,
                certificates: new CertificateCollection({
                    id: 0,
                    name: 'Certificate 1'
                }),
                certificate: new CertificateModel({signatories: []})
            });

            if (!disableSpy) {
                spyOn(view, 'addWindowActions');
            }

            return view;
        };

        var renderPage = function () {
            return initializePage().render();
        };

        beforeEach(function () {
            setFixtures(mockCertificatesPage);
            TemplateHelpers.installTemplates([
                'certificate-editor', 'certificate-details', 'signatory-details',
                'signatory-editor', 'list'
            ]);

            this.addMatchers({
                toBeExpanded: function () {
                    return Boolean($('a.signatory-toggle.hide-signatories', $(this.actual)).length);
                }
            });
        });

        describe('Initial display', function() {
            it('can render itself', function() {
                var view = initializePage();
                expect(view.$('.ui-loading')).toBeVisible();
                view.render();
                expect(view.$(certificateItemClassName)).toExist();
                expect(view.$('.signatories .no-content')).toExist();
                expect(view.$('.ui-loading')).toHaveClass('is-hidden');
            });
        });

        describe('Certificates', function() {
            beforeEach(function () {
                spyOn($.fn, 'focus');
                TemplateHelpers.installTemplate('certificate-details');
                this.view = initializePage(true);
            });

            it('should focus and expand if its id is part of url hash', function() {
                spyOn(this.view, 'getLocationHash').andReturn('#0');
                this.view.render();
                // We cannot use .toBeFocused due to flakiness.
                expect($.fn.focus).toHaveBeenCalled();
                expect(this.view.$(certificateItemClassName)).toBeExpanded();
            });

            it('should not focus on any certificate if url hash is empty', function() {
                spyOn(this.view, 'getLocationHash').andReturn('');
                this.view.render();
                expect($.fn.focus).not.toHaveBeenCalled();
                expect(this.view.$(certificateItemClassName)).not.toBeExpanded();
            });

            it('should not focus on any certificate if url hash contains wrong id', function() {
                spyOn(this.view, 'getLocationHash').andReturn('#1');
                this.view.render();
                expect($.fn.focus).not.toHaveBeenCalled();
                expect(this.view.$(certificateItemClassName)).not.toBeExpanded();
            });

            it('should not show a notification message if a certificate is not changed', function () {
                this.view.render();
                expect(this.view.onBeforeUnload()).toBeUndefined();
            });

            it('should show a notification message if a certificate is changed', function () {
                this.view.certificates.at(0).set('name', 'Certificate 2');
                expect(this.view.onBeforeUnload())
                    .toBe('You have unsaved changes. Do you really want to leave this page?');
            });
        });
    });
});
