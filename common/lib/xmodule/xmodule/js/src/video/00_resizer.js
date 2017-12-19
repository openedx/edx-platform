(function(requirejs, require, define) {
    define(
'video/00_resizer.js',
[],
function() {
    var Resizer = function(params) {
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

        var initialize = function(params) {
            if (!config) {
                config = defaults;
            }

            config = $.extend(true, {}, config, params);

            if (!config.element) {
                console.log(
                    'Required parameter `element` is not passed.'
                );
            }

            return module;
        };

        var getData = function() {
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

        var align = function() {
            var data = getData();

            switch (mode) {
            case 'height':
                alignByHeightOnly();
                break;

            case 'width':
                alignByWidthOnly();
                break;

            default:
                if (data.containerRatio >= data.elementRatio) {
                    alignByHeightOnly();
                } else {
                    alignByWidthOnly();
                }
                break;
            }

            fireCallbacks();

            return module;
        };

        var alignByWidthOnly = function() {
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

        var alignByHeightOnly = function() {
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

        var setMode = function(param) {
            if (_.isString(param)) {
                mode = param;
                align();
            }

            return module;
        };

        var setElement = function(element) {
            config.element = element;

            return module;
        };

        var addCallback = function(func) {
            if ($.isFunction(func)) {
                callbacksList.push(func);
            } else {
                console.error('[Video info]: TypeError: Argument is not a function.');
            }

            return module;
        };

        var addOnceCallback = function(func) {
            if ($.isFunction(func)) {
                var decorator = function() {
                    func();
                    removeCallback(func);
                };

                addCallback(decorator);
            } else {
                console.error('TypeError: Argument is not a function.');
            }

            return module;
        };

        var fireCallbacks = function() {
            $.each(callbacksList, function(index, callback) {
                callback();
            });
        };

        var removeCallbacks = function() {
            callbacksList.length = 0;

            return module;
        };

        var removeCallback = function(func) {
            var index = $.inArray(func, callbacksList);

            if (index !== -1) {
                return callbacksList.splice(index, 1);
            }
        };

        var resetDelta = function() {
            delta.height = delta.width = 0;

            return module;
        };

        var addDelta = function(value, side) {
            if (_.isNumber(value) && _.isNumber(delta[side])) {
                delta[side] += value;
            }

            return module;
        };

        var substractDelta = function(value, side) {
            if (_.isNumber(value) && _.isNumber(delta[side])) {
                delta[side] -= value;
            }

            return module;
        };

        var destroy = function() {
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
