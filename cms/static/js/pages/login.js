define(
    ['js/factories/login', 'common/js/utils/page_factory', 'js/factories/base'],
    function(LoginFactory, invokePageFactory) {
        'use strict';
        invokePageFactory('LoginFactory', LoginFactory);
    }
);

