(function($, JSON) {
    'use strict';

    var XBlock;

    function initializeBlockLikes(blockClass, initializer, element, requestToken) {
        var selector;
        requestToken = requestToken || $(element).data('request-token');
        if (requestToken) {
            selector = '.' + blockClass + '[data-request-token="' + requestToken + '"]';
        } else {
            selector = '.' + blockClass;
        }
        return $(element).immediateDescendents(selector).map(function(idx, elem) {
            return initializer(elem, requestToken);
        }).toArray();
    }

    function elementRuntime(element) {
        var $element = $(element),
            runtime = $element.data('runtime-class'),
            version = $element.data('runtime-version'),
            initFnName = $element.data('init');

        if (runtime && version && initFnName) {
            return new window[runtime]['v' + version]();
        } else {
            if (runtime || version || initFnName) {
                console.log(
                    'Block ' + $element.outerHTML + ' is missing data-runtime, data-runtime-version or data-init, ' +
                    'and can\'t be initialized'
                );
            } // else this XBlock doesn't have a JS init function.
            return null;
        }
    }

    function initArgs(element) {
        var initargs = $(element).children('.xblock-json-init-args').remove().text();
        return initargs ? JSON.parse(initargs) : {};
    }

    /**
     * Construct an XBlock family object from an element. The constructor
     * function is loaded from the 'data-init' attribute of the element.
     * The constructor is called with the arguments 'runtime', 'element',
     * and then all of 'block_args'.
     */
    function constructBlock(element, blockArgs) {
        var block;
        var $element = $(element);
        var runtime = elementRuntime(element);

        blockArgs.unshift(element);
        blockArgs.unshift(runtime);

        if (runtime) {
            block = (function() {
                var initFn = window[$element.data('init')];

                // This create a new constructor that can then apply() the block_args
                // to the initFn.
                function Block() {
                    return initFn.apply(this, blockArgs);
                }
                Block.prototype = initFn.prototype;

                return new Block();
            })();
            block.runtime = runtime;
        } else {
            block = {};
        }
        block.element = element;
        block.name = $element.data('name');
        block.type = $element.data('block-type');
        $element.trigger('xblock-initialized');
        $element.data('initialized', true);
        $element.addClass('xblock-initialized');
        return block;
    }

    XBlock = {
        Runtime: {},

        /**
         * Initialize the javascript for a single xblock element, and for all of it's
         * xblock children that match requestToken. If requestToken is omitted, use the
         * data-request-token attribute from element, or use the request-tokens specified on
         * the children themselves.
         */
        initializeBlock: function(element, requestToken) {
            var $element = $(element),
                children, asides;

            requestToken = requestToken || $element.data('request-token');
            children = XBlock.initializeXBlocks($element, requestToken);
            asides = XBlock.initializeXBlockAsides($element, requestToken);
            if (asides) {
                children = children.concat(asides);
            }
            $element.prop('xblock_children', children);

            return constructBlock(element, [initArgs(element)]);
        },

        /**
         * Initialize the javascript for a single xblock aside element that matches requestToken.
         * If requestToken is omitted, use the data-request-token attribute from element, or use
         * the request-tokens specified on the children themselves.
         */
        initializeAside: function(element) {
            var blockUsageId = $(element).data('block-id');
            var blockElement = $(element).siblings('[data-usage-id="' + blockUsageId + '"]')[0];
            return constructBlock(element, [blockElement, initArgs(element)]);
        },

        /**
         * Initialize all XBlocks inside element that were rendered with requestToken.
         * If requestToken is omitted, and element has a 'data-request-token' attribute, use that.
         * If neither is available, then use the request tokens of the immediateDescendent xblocks.
         */
        initializeXBlocks: function(element, requestToken) {
            return initializeBlockLikes('xblock', XBlock.initializeBlock, element, requestToken);
        },

        /**
         * Initialize all XBlockAsides inside element that were rendered with requestToken.
         * If requestToken is omitted, and element has a 'data-request-token' attribute, use that.
         * If neither is available, then use the request tokens of the immediateDescendent xblocks.
         */
        initializeXBlockAsides: function(element, requestToken) {
            return initializeBlockLikes('xblock_asides-v1', XBlock.initializeAside, element, requestToken);
        },

        /**
         * Initialize all XBlock-family blocks inside element that were rendered with requestToken.
         * If requestToken is omitted, and element has a 'data-request-token' attribute, use that.
         * If neither is available, then use the request tokens of the immediateDescendent xblocks.
         */
        initializeBlocks: function(element, requestToken) {
            var asides = XBlock.initializeXBlockAsides(element, requestToken);
            var xblocks = XBlock.initializeXBlocks(element, requestToken);
            if (asides) {
                xblocks = xblocks.concat(asides);
            }
            return xblocks;
        }
    };

    this.XBlock = XBlock;
}).call(this, $, JSON);
