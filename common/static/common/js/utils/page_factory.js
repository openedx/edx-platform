define([], function() {
    'use strict';

    return function invokePageFactory(name, factory) {
        var args;

        if (typeof window.pageFactoryArguments === 'undefined') {
            throw Error(
                'window.pageFactoryArguments must be initialized before calling invokePageFactory(' +
                name +
                '). Use the <%static:invoke_page_bundle> template tag.'
            );
        }
        args = window.pageFactoryArguments[name];

        if (typeof args === 'undefined') {
            throw Error(
                'window.pageFactoryArguments["' +
                name +
                '"] must be initialized before calling invokePageFactory(' +
                name +
                '). Use the <%static:invoke_page_bundle> template tag.'
            );
        }
        factory.apply(null, window.pageFactoryArguments[name]);
    };
});
