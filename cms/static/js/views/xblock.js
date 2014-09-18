define(["jquery", "underscore", "js/views/baseview", "xblock/runtime.v1"],
    function ($, _, BaseView, XBlock) {

        var XBlockView = BaseView.extend({
            // takes XBlockInfo as a model

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.view = this.options.view;
            },

            render: function(options) {
                var self = this,
                    view = this.view,
                    xblockInfo = this.model,
                    xblockUrl = xblockInfo.url();
                return $.ajax({
                    url: decodeURIComponent(xblockUrl) + "/" + view,
                    type: 'GET',
                    cache: false,
                    headers: { Accept: 'application/json' },
                    success: function(fragment) {
                        self.handleXBlockFragment(fragment, options);
                    }
                });
            },

            handleXBlockFragment: function(fragment, options) {
                var self = this,
                    wrapper = this.$el,
                    xblockElement,
                    successCallback = options ? options.success || options.done : null,
                    errorCallback = options ? options.error || options.done : null,
                    xblock,
                    fragmentsRendered;

                fragmentsRendered = this.renderXBlockFragment(fragment, wrapper);
                fragmentsRendered.always(function() {
                    xblockElement = self.$('.xblock').first();
                    try {
                        xblock = XBlock.initializeBlock(xblockElement);
                        self.xblock = xblock;
                        self.xblockReady(xblock);
                        if (successCallback) {
                            successCallback(xblock);
                        }
                    } catch (e) {
                        console.error(e.stack);
                        // Add 'xblock-initialization-failed' class to every xblock
                        self.$('.xblock').addClass('xblock-initialization-failed');

                        // If the xblock was rendered but failed then still call xblockReady to allow
                        // drag-and-drop to be initialized.
                        if (xblockElement) {
                            self.xblockReady(null);
                        }
                        if (errorCallback) {
                            errorCallback();
                        }
                    }
                });
            },

            /**
             * Sends a notification event to the runtime, if one is available. Note that the runtime
             * is only available once the xblock has been rendered and successfully initialized.
             * @param eventName The name of the event to be fired.
             * @param data The data to be passed to any listener's of the event.
             */
            notifyRuntime: function(eventName, data) {
                var runtime = this.xblock && this.xblock.runtime;
                if (runtime) {
                    runtime.notify(eventName, data);
                }
            },

            /**
             * This method is called upon successful rendering of an xblock. Note that the xblock
             * may have thrown JavaScript errors after rendering in which case the xblock parameter
             * will be null.
             */
            xblockReady: function(xblock) {
                // Do nothing
            },

            /**
             * Renders an xblock fragment into the specified element. The fragment has two attributes:
             *   html: the HTML to be rendered
             *   resources: any JavaScript or CSS resources that the HTML depends upon
             * Note that the XBlock is rendered asynchronously, and so a promise is returned that
             * represents this process.
             * @param fragment The fragment returned from the xblock_handler
             * @param element The element into which to render the fragment (defaults to this.$el)
             * @returns {jQuery promise} A promise representing the rendering process
             */
            renderXBlockFragment: function(fragment, element) {
                var html = fragment.html,
                    resources = fragment.resources;
                if (!element) {
                    element = this.$el;
                }

                // Render the HTML first as the scripts might depend upon it, and then
                // asynchronously add the resources to the page. Any errors that are thrown
                // by included scripts are logged to the console but are then ignored assuming
                // that at least the rendered HTML will be in place.
                try {
                    this.updateHtml(element, html);
                    return this.addXBlockFragmentResources(resources);
                } catch(e) {
                    console.error(e.stack);
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
             * @returns {jQuery promise} A promise representing the rendering process
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
             * @returns {jQuery promise} A promise representing the loading of the resource.
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
                        // Return a promise for the script resolution
                        return $.getScript(data);
                    }
                } else if (mimetype === "text/html") {
                    if (placement === "head") {
                        head.append(data);
                    }
                }
                // Return an already resolved promise for synchronous updates
                return $.Deferred().resolve().promise();
            }
        });

        return XBlockView;
    }); // end define();
