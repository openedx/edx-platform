define(
    ['js/factories/textbooks', 'common/js/utils/page_factory', 'js/pages/course'],
    function(TextbooksFactory, invokePageFactory) {
        'use strict';
        invokePageFactory('TextbooksFactory', TextbooksFactory);
    }
);
