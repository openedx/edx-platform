define(
    ['js/factories/login', 'common/js/utils/page_factory'],
    function(LoginFactory, invokePageFactory) {
        'use strict';
        invokePageFactory('LoginFactory', LoginFactory);
    }
);

