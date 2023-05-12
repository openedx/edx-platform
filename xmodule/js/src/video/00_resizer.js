(function(requirejs, require, define) {
    define(
        'video/00_resizer.js',
        [],
        function() {
            /* eslint-disable-next-line no-unused-vars, no-var */
            var Resizer = function(params) {
                // eslint-disable-next-line no-var
                var defaults = {
                        container: window,
                        element: null,
                        containerRatio: null,
                        elementRatio: null
                    },
                    callbacksList = [],
                    delta = {
                        height: 0,
                        width: 0
                    },
                    module = {},
                    mode = null,
                    config;

                /* eslint-disable-next-line no-shadow, no-var */
                var initialize = function(params) {
                    if (!config) {
                        config = defaults;
                    }

                    config = $.extend(true, {}, config, params);

                    if (!config.element) {
                        // eslint-disable-next-line no-console
                        console.log(
                            'Required parameter `element` is not passed.'
                        );
                    }

                    return module;
                };

                // eslint-disable-next-line no-var
                var getData = function() {
                    // eslint-disable-next-line no-var
                    var $container = $(config.container),
                        containerWidth = $container.width() + delta.width,
                        containerHeight = $container.height() + delta.height,
                        containerRatio = config.containerRatio,

                        $element = $(config.element),
                        elementRatio = config.elementRatio;

                    if (!containerRatio) {
                        containerRatio = containerWidth / containerHeight;
                    }

                    if (!elementRatio) {
                        elementRatio = $element.width() / $element.height();
                    }

                    return {
                        containerWidth: containerWidth,
                        containerHeight: containerHeight,
                        containerRatio: containerRatio,
                        element: $element,
                        elementRatio: elementRatio
                    };
                };

                // eslint-disable-next-line no-var
                var align = function() {
                    // eslint-disable-next-line no-var
                    var data = getData();

                    switch (mode) {
                    case 'height':
                        // eslint-disable-next-line no-use-before-define
                        alignByHeightOnly();
                        break;

                    case 'width':
                        // eslint-disable-next-line no-use-before-define
                        alignByWidthOnly();
                        break;

                    default:
                        if (data.containerRatio >= data.elementRatio) {
                            // eslint-disable-next-line no-use-before-define
                            alignByHeightOnly();
                        } else {
                            // eslint-disable-next-line no-use-before-define
                            alignByWidthOnly();
                        }
                        break;
                    }

                    // eslint-disable-next-line no-use-before-define
                    fireCallbacks();

                    return module;
                };

                // eslint-disable-next-line no-var
                var alignByWidthOnly = function() {
                    // eslint-disable-next-line no-var
                    var data = getData(),
                        height = data.containerWidth / data.elementRatio;

                    data.element.css({
                        height: height,
                        width: data.containerWidth,
                        top: 0.5 * (data.containerHeight - height),
                        left: 0
                    });

                    return module;
                };

                // eslint-disable-next-line no-var
                var alignByHeightOnly = function() {
                    // eslint-disable-next-line no-var
                    var data = getData(),
                        width = data.containerHeight * data.elementRatio;

                    data.element.css({
                        height: data.containerHeight,
                        width: data.containerHeight * data.elementRatio,
                        top: 0,
                        left: 0.5 * (data.containerWidth - width)
                    });

                    return module;
                };

                // eslint-disable-next-line no-var
                var setMode = function(param) {
                    // eslint-disable-next-line no-undef
                    if (_.isString(param)) {
                        mode = param;
                        align();
                    }

                    return module;
                };

                // eslint-disable-next-line no-var
                var setElement = function(element) {
                    config.element = element;

                    return module;
                };

                // eslint-disable-next-line no-var
                var addCallback = function(func) {
                    if ($.isFunction(func)) {
                        callbacksList.push(func);
                    } else {
                        // eslint-disable-next-line no-console
                        console.error('[Video info]: TypeError: Argument is not a function.');
                    }

                    return module;
                };

                // eslint-disable-next-line no-var
                var addOnceCallback = function(func) {
                    if ($.isFunction(func)) {
                        // eslint-disable-next-line no-var
                        var decorator = function() {
                            func();
                            // eslint-disable-next-line no-use-before-define
                            removeCallback(func);
                        };

                        addCallback(decorator);
                    } else {
                        // eslint-disable-next-line no-console
                        console.error('TypeError: Argument is not a function.');
                    }

                    return module;
                };

                // eslint-disable-next-line no-var
                var fireCallbacks = function() {
                    $.each(callbacksList, function(index, callback) {
                        callback();
                    });
                };

                // eslint-disable-next-line no-var
                var removeCallbacks = function() {
                    callbacksList.length = 0;

                    return module;
                };

                /* eslint-disable-next-line consistent-return, no-var */
                var removeCallback = function(func) {
                    // eslint-disable-next-line no-var
                    var index = $.inArray(func, callbacksList);

                    if (index !== -1) {
                        return callbacksList.splice(index, 1);
                    }
                };

                // eslint-disable-next-line no-var
                var resetDelta = function() {
                    // eslint-disable-next-line no-multi-assign
                    delta.height = delta.width = 0;

                    return module;
                };

                // eslint-disable-next-line no-var
                var addDelta = function(value, side) {
                    // eslint-disable-next-line no-undef
                    if (_.isNumber(value) && _.isNumber(delta[side])) {
                        delta[side] += value;
                    }

                    return module;
                };

                // eslint-disable-next-line no-var
                var substractDelta = function(value, side) {
                    // eslint-disable-next-line no-undef
                    if (_.isNumber(value) && _.isNumber(delta[side])) {
                        delta[side] -= value;
                    }

                    return module;
                };

                // eslint-disable-next-line no-var
                var destroy = function() {
                    // eslint-disable-next-line no-var
                    var data = getData();
                    data.element.css({
                        height: '', width: '', top: '', left: ''
                    });
                    removeCallbacks();
                    resetDelta();
                    mode = null;
                };

                initialize.apply(module, arguments);

                return $.extend(true, module, {
                    align: align,
                    alignByWidthOnly: alignByWidthOnly,
                    alignByHeightOnly: alignByHeightOnly,
                    destroy: destroy,
                    setParams: initialize,
                    setMode: setMode,
                    setElement: setElement,
                    callbacks: {
                        add: addCallback,
                        once: addOnceCallback,
                        remove: removeCallback,
                        removeAll: removeCallbacks
                    },
                    delta: {
                        add: addDelta,
                        substract: substractDelta,
                        reset: resetDelta
                    }
                });
            };

            return Resizer;
        });
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
