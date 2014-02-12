(function (requirejs, require, define) {

define(
'video/00_resizer.js',
[],
function () {

    var Resizer = function (params) {
        this.defaults = {
            container: window,
            element: null,
            containerRatio: null,
            elementRatio: null
        };
        this.callbacksList = [];
        this.mode = null;
        this.config = null;

        initialize.apply(this, arguments);

        this.setParams = initialize;
        this.callbacks = {
            add: _.bind(addCallback, this),
            once: _.bind(addOnceCallback, this),
            remove: _.bind(removeCallback, this),
            removeAll: _.bind(removeCallbacks, this)
        };
    };

    Resizer.prototype = {
        initialize: initialize,
        getData: getData,
        align: align,
        alignByWidthOnly: alignByWidthOnly,
        alignByHeightOnly: alignByHeightOnly,
        setMode: setMode,
        addCallback: addCallback,
        addOnceCallback: addOnceCallback,
        fireCallbacks: fireCallbacks,
        removeCallbacks: removeCallbacks,
        removeCallback: removeCallback
    };

    return Resizer;

    function initialize(params) {
        if (this.config) {
            this.config = $.extend(true, this.config, params);
        } else {
            this.config = $.extend(true, {}, this.defaults, params);
        }

        if (!this.config.element) {
            console.log(
                '[Video info]: Required parameter `element` is not passed.'
            );
        }

        return this;
    }

    function getData() {
        var container = $(this.config.container),
            containerWidth = container.width(),
            containerHeight = container.height(),
            containerRatio = this.config.containerRatio,

            element = $(this.config.element),
            elementRatio = this.config.elementRatio;

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
    }

    function align() {
        var data = this.getData();

        switch (this.mode) {
            case 'height':
                this.alignByHeightOnly();
                break;

            case 'width':
                this.alignByWidthOnly();
                break;

            default:
                if (data.containerRatio >= data.elementRatio) {
                    this.alignByHeightOnly();

                } else {
                    this.alignByWidthOnly();
                }
                break;
        }

        this.fireCallbacks();

        return this;
    }

    function alignByWidthOnly() {
        var data = this.getData(),
            height = data.containerWidth/data.elementRatio;

        data.element.css({
            'height': height,
            'width': data.containerWidth,
            'top': 0.5*(data.containerHeight - height),
            'left': 0
        });

        return this;
    }

    function alignByHeightOnly() {
        var data = this.getData(),
            width = data.containerHeight*data.elementRatio;

        data.element.css({
            'height': data.containerHeight,
            'width': data.containerHeight*data.elementRatio,
            'top': 0,
            'left': 0.5*(data.containerWidth - width)
        });

        return this;
    }

    function setMode(param) {
        if (_.isString(param)) {
            this.mode = param;
            this.align();
        }

        return this;
    }

    function addCallback(func) {
        if ($.isFunction(func)) {
            this.callbacksList.push(func);
        } else {
            console.error('[Video info]: TypeError: Argument is not a function.');
        }

        return this;
    }

    function addOnceCallback(func) {
        console.log('[addOnceCallback]: this = ', this);

        if ($.isFunction(func)) {
            var decorator = function () {
                func();
                this.removeCallback(func);
            };

            this.addCallback(decorator);
        } else {
            console.error('[Video info]: TypeError: Argument is not a function.');
        }

        return this;
    }

    function fireCallbacks() {
        var _this = this;

        $.each(this.callbacksList, function(index, callback) {
             callback.apply(_this);
        });
    }

    function removeCallbacks() {
        this.callbacksList.length = 0;

        return this;
    }

    function removeCallback(func) {
        var index = $.inArray(func, this.callbacksList);

        if (index !== -1) {
            return this.callbacksList.splice(index, 1);
        }
    }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
