define([], function() {
    'use strict';

    return function invokePageFactory(factory) {
        var args;

        if (typeof window.pageFactoryArguments === 'undefined') {
            throw Error(
                'window.pageFactoryArguments must be initialized before calling invokePageFactory(' +
                factory.name +
                '). Use the <%static:require_page> template tag.'
            );
        }
        args = window.pageFactoryArguments[factory.name];

        if (typeof args === 'undefined') {
            throw Error(
                'window.pageFactoryArguments["' +
                factory.name +
                '"] must be initialized before calling invokePageFactory(' +
                factory.name +
                '). Use the <%static:require_page> template tag.'
            );
        }
        factory.apply(window.pageFactoryArguments[factory.name]);
    };
});
