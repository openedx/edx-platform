(function(define) {
    'use strict';

    define(
        ['js/certificates/factories/certificates_page_factory', 'common/js/utils/page_factory'],
        function(CertificatesPageFactory, invokePageFactory) {
            invokePageFactory('CertificatesPageFactory', CertificatesPageFactory);
        }
    );
}).call(this, define || RequireJS.define);
