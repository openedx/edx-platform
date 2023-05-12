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
        // eslint-disable-next-line camelcase
        return function(certificate_allowlist_json, generate_certificate_exceptions_url,
            // eslint-disable-next-line camelcase
            certificate_exception_view_url, generate_bulk_certificate_exceptions_url,
            // eslint-disable-next-line camelcase
            active_certificate) {
            var certificateAllowlist = new CertificateAllowlistCollection(certificate_allowlist_json, {
                parse: true,
                canBeEmpty: true,
                // eslint-disable-next-line camelcase
                url: certificate_exception_view_url,
                // eslint-disable-next-line camelcase
                generate_certificates_url: generate_certificate_exceptions_url
            });

            var certificateAllowlistEditorView = new CertificateAllowlistEditorView({
                collection: certificateAllowlist
            });
            certificateAllowlistEditorView.render();

            new CertificateAllowlistView({
                collection: certificateAllowlist,
                certificateAllowlistEditorView: certificateAllowlistEditorView,
                // eslint-disable-next-line camelcase
                active_certificate: active_certificate
            }).render();

            new CertificateBulkAllowlist({
                // eslint-disable-next-line camelcase
                bulk_exception_url: generate_bulk_certificate_exceptions_url
            }).render();
        };
    }
    );
}).call(this, define || RequireJS.define);
