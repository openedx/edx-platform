define(
    ['js/factories/container', 'common/js/utils/page_factory', 'js/factories/base', 'js/pages/course'],
    function(ContainerFactory, invokePageFactory) {
        'use strict';
        invokePageFactory('ContainerFactory', ContainerFactory);
    }
);

