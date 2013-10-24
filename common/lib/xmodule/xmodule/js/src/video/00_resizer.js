(function (requirejs, require, define) {

define(
'video/00_resizer.js',
[],
function () {

    var Resizer = function (params) {
        var defaults = {
                container: window,
                element: null,
                containerRatio: null,
                elementRatio: null
            },
            mode = null,
            config;

        var initialize = function (params) {
            if (config) {
                config = $.extend(true, config, params);
            } else {
                config = $.extend(true, {}, defaults, params);
            }

            if (!config.element) {
                console.log(
                    '[Video info]: Required parameter `element` is not passed.'
                );
            }

            return this;
        };

        var getData = function () {
            var container = $(config.container),
                containerWidth = container.width(),
                containerHeight = container.height(),
                containerRatio = config.containerRatio,

                element = $(config.element),
                elementRatio = config.elementRatio;

            if (!containerRatio) {
                containerRatio = containerWidth/containerHeight;
            }

            if (!elementRatio) {
                elementRatio = element.width()/element.height();
            }

            return {
                containerWidth: containerWidth,
                containerHeight: containerHeight,
                containerRatio: containerRatio,
                element: element,
                elementRatio: elementRatio
            };
        };

        var align = function () {
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

            return this;
        };

        var alignByWidthOnly = function () {
            var data = getData(),
                height = data.containerWidth/data.elementRatio;

            data.element.css({
                'height': height,
                'width': data.containerWidth,
                'top': 0.5*(data.containerHeight - height),
                'left': 0
            });

            return this;
        };

        var alignByHeightOnly = function () {
            var data = getData(),
                width = data.containerHeight*data.elementRatio;

            data.element.css({
                'height': data.containerHeight,
                'width': data.containerHeight*data.elementRatio,
                'top': 0,
                'left': 0.5*(data.containerWidth - width)
            });

            return this;
        };

        var setMode = function (param) {
            if (_.isString(param)) {
                mode = param;
                align();
            }

            return this;
        };

        initialize.apply(this, arguments);

        return {
            align: align,
            alignByWidthOnly: alignByWidthOnly,
            alignByHeightOnly: alignByHeightOnly,
            setParams: initialize,
            setMode: setMode
        };
    };

    return Resizer;
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
