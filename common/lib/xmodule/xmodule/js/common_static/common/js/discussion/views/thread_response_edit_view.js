/* globals DiscussionUtil */
(function() {
    'use strict';
    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            for (var key in parent) {
                if (__hasProp.call(parent, key)) {
                    child[key] = parent[key];
                }
            }
            function ctor() {
                this.constructor = child;
            }

            ctor.prototype = parent.prototype;
            child.prototype = new ctor();
            child.__super__ = parent.prototype;
            return child;
        };

    if (typeof Backbone !== 'undefined' && Backbone !== null) {
        this.ThreadResponseEditView = (function(_super) {
            __extends(ThreadResponseEditView, _super);

            function ThreadResponseEditView() {
                return ThreadResponseEditView.__super__.constructor.apply(this, arguments);
            }

            ThreadResponseEditView.prototype.events = {
                'click .post-update': 'update',
                'click .post-cancel': 'cancel_edit'
            };

            ThreadResponseEditView.prototype.$ = function(selector) {
                return this.$el.find(selector);
            };

            ThreadResponseEditView.prototype.initialize = function(options) {
                this.options = options;
                return ThreadResponseEditView.__super__.initialize.call(this);
            };

            ThreadResponseEditView.prototype.render = function() {
                var context = $.extend({mode: this.options.mode, startHeader: this.options.startHeader},
                    this.model.attributes);
                this.template = edx.HtmlUtils.template($('#thread-response-edit-template').html());
                edx.HtmlUtils.setHtml(
                    this.$el,
                    this.template(context)
                );
                this.delegateEvents();
                DiscussionUtil.makeWmdEditor(this.$el, $.proxy(this.$, this), 'edit-post-body');
                return this;
            };

            ThreadResponseEditView.prototype.update = function(event) {
                return this.trigger('response:update', event);
            };

            ThreadResponseEditView.prototype.cancel_edit = function(event) {
                return this.trigger('response:cancel_edit', event);
            };

            return ThreadResponseEditView;
        }(Backbone.View));
    }
}).call(window);
