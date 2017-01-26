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
                this.template = _.template($("#response-comment-show-template").html());
                this.$el.html(this.template(_.extend({
                    cid: this.model.cid,
                    author_display: this.getAuthorDisplay(),
                    readOnly: $('.discussion-module').data('read-only')
                }, this.model.attributes)));
                this.delegateEvents();
                this.renderAttrs();
                this.$el.find(".timeago").timeago();
                this.convertMath();
                this.addReplyLink();
                return this;
            };

            ResponseCommentShowView.prototype.addReplyLink = function() {
                var html, name, p, _ref;
                if (this.model.hasOwnProperty('parent')) {
                    name = (_ref = this.model.parent.get('username')) !== null ? _ref : gettext("anonymous");
                    html = "<a href='#comment_" + this.model.parent.id + "'>@" + name + "</a>:  ";
                    p = this.$('.response-body p:first');
                    return p.prepend(html);
                }
            };

            ResponseCommentShowView.prototype.convertMath = function() {
                var body;
                body = this.$el.find(".response-body");
                body.html(DiscussionUtil.postMathJaxProcessor(DiscussionUtil.markdownWithHighlight(body.text())));
                if (typeof MathJax !== "undefined" && MathJax !== null) {
                    return MathJax.Hub.Queue(["Typeset", MathJax.Hub, body[0]]);
                }
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
