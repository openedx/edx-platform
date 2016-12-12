define(['jquery', 'underscore', 'common/js/components/utils/view_utils', 'js/views/baseview', 'xblock/runtime.v1'],
    function($, _, ViewUtils, BaseView, XBlock) {
        'use strict';

        var XBlockView = BaseView.extend({
            // takes XBlockInfo as a model

            events: {
                'click .notification-action-button': 'fireNotificationActionEvent'
            },

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
                    url: decodeURIComponent(xblockUrl) + '/' + view,
                    type: 'GET',
                    cache: false,
                    headers: {Accept: 'application/json'},
                    success: function(fragment) {
                        self.handleXBlockFragment(fragment, options);
                    }
                });
            },

            initRuntimeData: function(xblock, options) {
                if (options && options.initRuntimeData && xblock && xblock.runtime && !xblock.runtime.page) {
                    xblock.runtime.page = options.initRuntimeData;
                }
                return xblock;
            },

            handleXBlockFragment: function(fragment, options) {
                var self = this,
                    wrapper = this.$el,
                    xblockElement,
                    successCallback = options ? options.success || options.done : null,
                    errorCallback = options ? options.error || options.done : null,
                    xblock,
                    fragmentsRendered;

                fragmentsRendered = XBlock.renderXBlockFragment(fragment, wrapper);
                fragmentsRendered.always(function() {
                    xblockElement = self.$('.xblock').first();
                    try {
                        xblock = XBlock.initializeBlock(xblockElement);
                        self.xblock = self.initRuntimeData(xblock, options);
                        self.xblockReady(self.xblock);
                        self.$('.xblock_asides-v1').each(function() {
                            if (!$(this).hasClass('xblock-initialized')) {
                                var aside = XBlock.initializeBlock($(this));
                                self.initRuntimeData(aside, options);
                            }
                        });
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
                } else if (this.xblock) {
                    var xblock_children = this.xblock.element && $(this.xblock.element).prop('xblock_children');
                    if (xblock_children) {
                        $(xblock_children).each(function() {
                            if (this.runtime) {
                                this.runtime.notify(eventName, data);
                            }
                        });
                    }
                }
            },

            /**
             * This method is called upon successful rendering of an xblock. Note that the xblock
             * may have thrown JavaScript errors after rendering in which case the xblock parameter
             * will be null.
             */
            xblockReady: function(xblock) {  // eslint-disable-line no-unused-vars
                // Do nothing
            },

            fireNotificationActionEvent: function(event) {
                var eventName = $(event.currentTarget).data('notification-action');
                if (eventName) {
                    event.preventDefault();
                    this.notifyRuntime(eventName, this.model.get('id'));
                }
            }
        });

        return XBlockView;
    }); // end define();
