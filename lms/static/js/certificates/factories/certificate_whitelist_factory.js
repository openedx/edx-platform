// Backbone.js Page Object Factory: Certificates
/*global define, RequireJS */

;(function(define){
    'use strict';
    define([
            'jquery',
            'js/certificates/views/certificate_whitelist',
            'js/certificates/models/certificate_exception',
            'js/certificates/views/certificate_whitelist_editor',
            'js/certificates/collections/certificate_whitelist'
        ],
        function($, CertificateWhiteListListView, CertificateExceptionModel, CertificateWhiteListEditorView ,
                 CertificateWhiteListCollection){
            return function(certificate_white_list_json, generate_certificate_exceptions_url,
                            certificate_exception_view_url){

                var certificateWhiteList = new CertificateWhiteListCollection(JSON.parse(certificate_white_list_json), {
                    parse: true,
                    canBeEmpty: true,
                    url: certificate_exception_view_url,
                    generate_certificates_url: generate_certificate_exceptions_url
                });

                var certificateWhiteListEditorView = new CertificateWhiteListEditorView({
                    collection: certificateWhiteList
                });
                certificateWhiteListEditorView.render();

                new CertificateWhiteListListView({
                    collection: certificateWhiteList,
                    certificateWhiteListEditorView: certificateWhiteListEditorView
                }).render();

            };
        }
    );
}).call(this, define || RequireJS.define);