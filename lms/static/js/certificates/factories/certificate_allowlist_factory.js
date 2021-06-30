// Backbone.js Page Object Factory: Certificates
/* global define, RequireJS */

(function(define) {
    'use strict';
    define([
        'jquery',
        'js/certificates/views/certificate_allowlist',
        'js/certificates/models/certificate_exception',
        'js/certificates/views/certificate_allowlist_editor',
        'js/certificates/collections/certificate_allowlist',
        'js/certificates/views/certificate_bulk_allowlist'
    ],
        function($, CertificateAllowlistView, CertificateExceptionModel, CertificateAllowlistEditorView,
                 CertificateAllowlistCollection, CertificateBulkAllowlist) {
            return function(certificate_allowlist_json, generate_certificate_exceptions_url,
                            certificate_exception_view_url, generate_bulk_certificate_exceptions_url,
                            active_certificate) {
                var certificateAllowlist = new CertificateAllowlistCollection(certificate_allowlist_json, {
                    parse: true,
                    canBeEmpty: true,
                    url: certificate_exception_view_url,
                    generate_certificates_url: generate_certificate_exceptions_url
                });

                var certificateAllowlistEditorView = new CertificateAllowlistEditorView({
                    collection: certificateAllowlist
                });
                certificateAllowlistEditorView.render();

                new CertificateAllowlistView({
                    collection: certificateAllowlist,
                    certificateAllowlistEditorView: certificateAllowlistEditorView,
                    active_certificate: active_certificate
                }).render();

                new CertificateBulkAllowlist({
                    bulk_exception_url: generate_bulk_certificate_exceptions_url
                }).render();
            };
        }
    );
}).call(this, define || RequireJS.define);
