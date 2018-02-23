define(
    ['js/factories/library', 'common/js/utils/page_factory', 'js/factories/base'],
    function(LibraryFactory, invokePageFactory) {
        'use strict';
        invokePageFactory('LibraryFactory', LibraryFactory);
    }
);

