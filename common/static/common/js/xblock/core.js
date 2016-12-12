(function($, JSON, require) {
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
         * Renders an xblock fragment into the specified element. The fragment has two attributes:
         *   html: the HTML to be rendered
         *   resources: any JavaScript or CSS resources that the HTML depends upon
         * Note that the XBlock is rendered asynchronously, and so a promise is returned that
         * represents this process.
         * @param fragment The fragment returned from the xblock_handler
         * @param element The element into which to render the fragment (defaults to this.$el)
         * @returns {Promise} A promise representing the rendering process
         */
        renderXBlockFragment: function(fragment, element) {
            var html = fragment.html,
                resources = fragment.resources;

            // Render the HTML first as the scripts might depend upon it, and then
            // asynchronously add the resources to the page. Any errors that are thrown
            // by included scripts are logged to the console but are then ignored assuming
            // that at least the rendered HTML will be in place.
            try {
                this.updateHtml(element, html);
                return this.addXBlockFragmentResources(resources);
            } catch(e) {
                console.error(e, e.stack);
                return $.Deferred().resolve();
            }
        },

        /**
         * Updates an element to have the specified HTML. The default method sets the HTML
         * as child content, but this can be overridden.
         * @param element The element to be updated
         * @param html The desired HTML.
         */
        updateHtml: function(element, html) {
            element.html(html);
        },

        /**
         * Dynamically loads all of an XBlock's dependent resources. This is an asynchronous
         * process so a promise is returned.
         * @param resources The resources to be rendered
         * @returns {Promise} A promise representing the rendering process
         */
        addXBlockFragmentResources: function(resources) {
            var self = this,
                applyResource,
                numResources,
                deferred;
            numResources = resources.length;
            deferred = $.Deferred();
            applyResource = function(index) {
                var hash, resource, value, promise;
                if (index >= numResources) {
                    deferred.resolve();
                    return;
                }
                value = resources[index];
                hash = value[0];
                if (!window.loadedXBlockResources) {
                    window.loadedXBlockResources = [];
                }
                if (_.indexOf(window.loadedXBlockResources, hash) < 0) {
                    resource = value[1];
                    promise = self.loadResource(resource);
                    window.loadedXBlockResources.push(hash);
                    promise.done(function() {
                        applyResource(index + 1);
                    }).fail(function() {
                        deferred.reject();
                    });
                } else {
                    applyResource(index + 1);
                }
            };
            applyResource(0);
            return deferred.promise();
        },

        /**
         * Loads the specified resource into the page.
         * @param resource The resource to be loaded.
         * @returns {Promise} A promise representing the loading of the resource.
         */
        loadResource: function(resource) {
            var head = $('head'),
                mimetype = resource.mimetype,
                kind = resource.kind,
                placement = resource.placement,
                data = resource.data;
            if (mimetype === "text/css") {
                if (kind === "text") {
                    head.append("<style type='text/css'>" + data + "</style>");
                } else if (kind === "url") {
                    head.append("<link rel='stylesheet' href='" + data + "' type='text/css'>");
                }
            } else if (mimetype === "application/javascript") {
                if (kind === "text") {
                    head.append("<script>" + data + "</script>");
                } else if (kind === "url") {
                    return this.loadJavaScript(data);
                }
            } else if (mimetype === "text/html") {
                if (placement === "head") {
                    head.append(data);
                }
            }
            // Return an already resolved promise for synchronous updates
            return $.Deferred().resolve().promise();
        },

        /**
         * Dynamically loads the specified JavaScript file.  This is a copy of
         * ViewUtils.loadJavaScript(), an interim solution that will eventually
         * be removed when this module is properly refactored into the
         * RequireJS framework.
         * @param url The URL to a JavaScript file.
         * @returns {Promise} A promise indicating when the URL has been loaded.
         */
        loadJavaScript: function(url) {
            var deferred = $.Deferred();
            require([url],
                function() {
                    deferred.resolve();
                },
                function() {
                    deferred.reject();
                });
            return deferred.promise();
        },

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
}).call(this, $, JSON, require || RequireJS.require);
