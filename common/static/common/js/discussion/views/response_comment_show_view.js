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
        this.ResponseCommentShowView = (function(_super) {

            __extends(ResponseCommentShowView, _super);

            function ResponseCommentShowView() {
                var self = this;
                this.edit = function() {
                    return ResponseCommentShowView.prototype.edit.apply(self, arguments);
                };
                this._delete = function() {
                    return ResponseCommentShowView.prototype._delete.apply(self, arguments);
                };
                return ResponseCommentShowView.__super__.constructor.apply(this, arguments);
            }

            ResponseCommentShowView.prototype.tagName = "li";

            ResponseCommentShowView.prototype.render = function() {
                var template = edx.HtmlUtils.template($("#response-comment-show-template").html());
                var context = _.extend({
                    cid: this.model.cid,
                    author_display: this.getAuthorDisplay(),
                    readOnly: $('.discussion-module').data('read-only')
                }, this.model.attributes);

                edx.HtmlUtils.setHtml(this.$el, template(context));
                this.delegateEvents();
                this.renderAttrs();
                this.$el.find(".timeago").timeago();
                this.convertMath();
                this.addReplyLink();
                return this;
            };

            ResponseCommentShowView.prototype.addReplyLink = function() {
                var html, name;
                if (this.model.hasOwnProperty('parent')) {
                    name = this.model.parent.get('username') || gettext("anonymous");
                    html = edx.HtmlUtils.interpolateHtml(
                        edx.HtmlUtils.HTML("<a href='#comment_{parent_id}'>@{name}</a>:  "),
                        {
                            parent_id: this.model.parent.id,
                            name: name
                        }
                    );
                    return edx.HtmlUtils.prepend(
                        this.$('.response-body p:first'),
                        html
                    );
                }
            };

            ResponseCommentShowView.prototype.convertMath = function() {
                DiscussionUtil.convertMath(this.$el.find(".response-body"));
            };

            ResponseCommentShowView.prototype._delete = function(event) {
                return this.trigger("comment:_delete", event);
            };

            ResponseCommentShowView.prototype.edit = function(event) {
                return this.trigger("comment:edit", event);
            };

            return ResponseCommentShowView;

        })(DiscussionContentShowView);
    }

}).call(window);
