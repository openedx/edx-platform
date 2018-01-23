define([], function() {
    'use strict';

    return function invokePageFactory(name, factory) {
        var args;

        if (typeof window.pageFactoryArguments === 'undefined') {
            throw Error(
                'window.pageFactoryArguments must be initialized before calling invokePageFactory(' +
                name +
                '). Use the <%static:require_page> template tag. Available keys are ' +
                window.pageFactoryArguments.keys()
            );
        }
        args = window.pageFactoryArguments[name];

        if (typeof args === 'undefined') {
            console.log('window.pageFactoryArguments', window.pageFactoryArguments);
            throw Error(
                'window.pageFactoryArguments["' +
                name +
                '"] must be initialized before calling invokePageFactory(' +
                name +
                '). Use the <%static:require_page> template tag. Available keys are ' +
                window.pageFactoryArguments.keys()
            );
        }
        factory.apply(null, window.pageFactoryArguments[name]);
    };
});
