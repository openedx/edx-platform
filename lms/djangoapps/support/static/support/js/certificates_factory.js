(function(define) {
    'use strict';

    define(['jquery', 'underscore', 'support/js/views/certificates'],
        function($, _, CertificatesView) {
            return function(options) {
                options = _.extend(options, {
                    el: $('.certificates-content')
                });
                return new CertificatesView(options).render();
            };
        });
}).call(this, define || RequireJS.define);
