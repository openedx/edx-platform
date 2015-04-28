/**
 * The basic idea of the page factories is that they are a single RequireJS dependency that can be loaded to create a page. This was put in place for RequireJS Optimizer, which needs to have a single root to determine statically all of the dependencies needed by a page. Optimizer takes all of the dependencies and puts them into a single optimized JS file.
 * You'll see that the Mako templates typically have a block that constructs the page using the factory
 * We write unit tests for them to verify that they behave as desired. Some of them are more complex than others.
 * RequireJS Optimizer is only enabled in Studio at the moment, so the factories aren't strictly required in the LMS. We do intend to enable it on the LMS too
 */
define([
    'js/certificates/collections/certificates', 'js/certificates/models/certificate', 'js/certificates/views/certificates_page'
], function(CertificatesCollection, Certificate, CertificatesPage) {
    'use strict';
    console.log("certficate_factory.start");
    return function (certificatesJson, certificateUrl, courseOutlineUrl) {
        console.log('certificate_factory.function.start');

        var certificatesCollection = new CertificatesCollection(certificatesJson, {
            parse: true,
            canBeEmpty: true,
            certificateUrl: certificateUrl
        });
        /*
        var certificatesCollection = new CertificatesCollection();
        certificatesCollection.url = certificateUrl;
        certificatesCollection.outlineUrl = courseOutlineUrl;
        */

        console.log("certificate_factory.certificateCollection");
        console.log(certificatesCollection);
        console.log("certificate_factory.CertificatesPage.render");
        var certificatesPage = new CertificatesPage({
            el: $('#content'),
            certificatesCollection: certificatesCollection
        }).render();
    };
});
