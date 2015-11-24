// Backbone.js Page Object Factory: Certificates
/*global define, RequireJS */

;(function(define){
    'use strict';
    define([
            'jquery',
            'js/certificates/views/certificate_bulk_whitelist',
            'js/certificates/views/certificate_whitelist',
            'js/certificates/models/certificate_exception',
            'js/certificates/views/certificate_whitelist_editor',
            'js/certificates/collections/certificate_whitelist'
        ],
        function($, CertificateBulkWhiteList, CertificateWhiteListListView, CertificateExceptionModel,
                 CertificateWhiteListEditorView , CertificateWhiteListCollection){
            return function(certificate_white_list_json, certificate_exception_url, bulk_certificate_exceptions_url){

                var certificateWhiteList = new CertificateWhiteListCollection(JSON.parse(certificate_white_list_json), {
                    parse: true,
                    canBeEmpty: true,
                    url: certificate_exception_url
                });

                new CertificateWhiteListListView({
                    collection: certificateWhiteList
                }).render();

                new CertificateWhiteListEditorView({
                    collection: certificateWhiteList
                }).render();

                new CertificateBulkWhiteList({
                    bulk_exception_url: bulk_certificate_exceptions_url
                }).render();

            };
        }
    );
}).call(this, define || RequireJS.define);