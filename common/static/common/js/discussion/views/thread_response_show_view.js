/* globals DiscussionContentShowView, DiscussionUtil, MathJax */
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

    if (typeof Backbone !== "undefined" && Backbone !== null) {
        this.ThreadResponseShowView = (function(_super) {

            __extends(ThreadResponseShowView, _super);

            function ThreadResponseShowView() {
                return ThreadResponseShowView.__super__.constructor.apply(this, arguments);
            }

            ThreadResponseShowView.prototype.initialize = function() {
                ThreadResponseShowView.__super__.initialize.call(this);
                return this.listenTo(this.model, "change", this.render);
            };

            ThreadResponseShowView.prototype.renderTemplate = function() {
                var template = edx.HtmlUtils.template($("#thread-response-show-template").html()),
                    context = _.extend({
                        cid: this.model.cid,
                        author_display: this.getAuthorDisplay(),
                        endorser_display: this.getEndorserDisplay(),
                        readOnly: $('.discussion-module').data('read-only')
                    }, this.model.attributes);
                return template(context);
            };

            ThreadResponseShowView.prototype.render = function() {
                edx.HtmlUtils.setHtml(this.$el, this.renderTemplate());
                this.delegateEvents();
                this.renderAttrs();
                this.$el.find(".posted-details .timeago").timeago();
                this.convertMath();
                return this;
            };

            ThreadResponseShowView.prototype.convertMath = function() {
                DiscussionUtil.convertMath(this.$(".response-body"));
            };

            ThreadResponseShowView.prototype.edit = function(event) {
                return this.trigger("response:edit", event);
            };

            ThreadResponseShowView.prototype._delete = function(event) {
                return this.trigger("response:_delete", event);
            };

            return ThreadResponseShowView;

        })(DiscussionContentShowView);
    }

}).call(window);
