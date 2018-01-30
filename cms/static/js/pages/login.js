(function(define) {
    'use strict';

    define(
        ['js/factories/login', 'common/js/utils/page_factory', 'js/factories/base'],
        function(LoginFactory, invokePageFactory) {
            invokePageFactory('LoginFactory', LoginFactory);
        }
    );
}).call(this, define || RequireJS.define);

