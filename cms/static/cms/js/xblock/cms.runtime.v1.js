define(['jquery', 'backbone', 'xblock/runtime.v1', 'URI', 'gettext', 'js/utils/modal',
        'common/js/components/views/feedback_notification'],
    function($, Backbone, XBlock, URI, gettext, ModalUtils, NotificationView) {
        'use strict';

        var __hasProp = {}.hasOwnProperty,
            __extends = function(child, parent) {
                var key;
                for (key in parent) {
                    if (__hasProp.call(parent, key)) {
                        child[key] = parent[key];
                    }
                }
                function Ctor() {
                    this.constructor = child;
                }
                Ctor.prototype = parent.prototype;
                child.prototype = new Ctor();
                child.__super__ = parent.prototype;
                return child;
            },
            BaseRuntime = {},
            PreviewRuntime = {},
            StudioRuntime = {};

        BaseRuntime.v1 = (function(_super) {

            __extends(v1, _super);

            v1.prototype.handlerUrl = function(element, handlerName, suffix, query) {
                var uri;
                uri = URI(this.handlerPrefix)
                    .segment($(element).data('usage-id'))
                    .segment('handler')
                    .segment(handlerName);
                if (suffix !== null) {
                    uri.segment(suffix);
                }
                if (query !== null) {
                    uri.search(query);
                }
                return uri.toString();
            };

            function v1() {
                v1.__super__.constructor.call(this);
                this.dispatcher = _.clone(Backbone.Events);
                this.listenTo('save', this._handleSave);
                this.listenTo('cancel', this._handleCancel);
                this.listenTo('error', this._handleError);
                this.listenTo('modal-shown', function(data) {
                    this.modal = data;
                });
                this.listenTo('modal-hidden', function() {
                    this.modal = null;
                });
                this.listenTo('page-shown', function(data) {
                    this.page = data;
                });
            }

            /**
             * Notify the Studio client-side runtime of an event so that it
             * can update the UI in a consistent way.
             *
             * @param {string} name The name of the event.
             * @param {object} data A JSON representation of the data to be included with the event.
             */
            v1.prototype.notify = function(name, data) {
                this.dispatcher.trigger(name, data);
            };

            /**
             * Listen to a Studio event and invoke the specified callback when it is triggered.
             *
             * @param {string} name The name of the event.
             * @param {function} callback The callback to be invoked.
             */
            v1.prototype.listenTo = function(name, callback) {
                this.dispatcher.bind(name, callback, this);
            };

            /**
             * Refresh the view for the xblock represented by the specified element.
             *
             * @param {element} element The element representing the XBlock.
             */
            v1.prototype.refreshXBlock = function(element) {
                if (this.page) {
                    this.page.refreshXBlock(element);
                }
            };

            v1.prototype._handleError = function(data) {
                var message, title;
                message = data.message || data.msg;
                if (message) {
                    // TODO: remove 'Open Assessment' specific default title
                    title = data.title || gettext('OpenAssessment Save Error');
                    this.alert = new NotificationView.Error({
                        title: title,
                        message: message,
                        closeIcon: false,
                        shown: false
                    });
                    this.alert.show();
                }
            };

            v1.prototype._handleSave = function(data) {
                var message;
                // Starting to save, so show a notification
                if (data.state === 'start') {
                    message = data.message || gettext('Saving');
                    this.notification = new NotificationView.Mini({
                        title: message
                    });
                    this.notification.show();
                } else if (data.state === 'end') {
                    // Finished saving, so hide the notification and refresh appropriately
                    this._hideAlerts();

                    if (this.modal && this.modal.onSave) {
                        // Notify the modal that the save has completed so that it can hide itself
                        // and then refresh the xblock.
                        this.modal.onSave();
                    } else if (data.element) {
                        // ... else ask it to refresh the newly saved xblock
                        this.refreshXBlock(data.element);
                    }
                    this.notification.hide();
                }
            };

            v1.prototype._handleCancel = function() {
                this._hideAlerts();
                if (this.modal) {
                    this.modal.cancel();
                    this.notify('modal-hidden');
                }
            };

            /**
             * Hide any alerts that are being shown.
             */
            v1.prototype._hideAlerts = function() {
                if (this.alert && this.alert.options.shown) {
                    this.alert.hide();
                }
            };

            return v1;

        })(XBlock.Runtime.v1);

        PreviewRuntime.v1 = (function(_super) {

            __extends(v1, _super);

            function v1() {
                return v1.__super__.constructor.apply(this, arguments);
            }

            v1.prototype.handlerPrefix = '/preview/xblock';

            return v1;

        })(BaseRuntime.v1);

        StudioRuntime.v1 = (function(_super) {

            __extends(v1, _super);

            function v1() {
                return v1.__super__.constructor.apply(this, arguments);
            }

            v1.prototype.handlerPrefix = '/xblock';

            return v1;

        })(BaseRuntime.v1);

        // Install the runtime's into the global namespace
        window.BaseRuntime = BaseRuntime;
        window.PreviewRuntime = PreviewRuntime;
        window.StudioRuntime = StudioRuntime;
    });
