define(
    ['js/factories/textbooks', 'common/js/utils/page_factory', 'js/factories/base', 'js/pages/course'],
    function(TextbooksFactory, invokePageFactory) {
        'use strict';
        invokePageFactory('TextbooksFactory', TextbooksFactory);
    }
);
