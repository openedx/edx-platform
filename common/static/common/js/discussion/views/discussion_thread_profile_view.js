/* globals DiscussionUtil, MathJax */
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
        this.DiscussionThreadProfileView = (function(_super) {

            __extends(DiscussionThreadProfileView, _super);

            function DiscussionThreadProfileView() {
                return DiscussionThreadProfileView.__super__.constructor.apply(this, arguments);
            }

            DiscussionThreadProfileView.prototype.render = function() {
                var element, params;
                this.convertMath();
                this.abbreviateBody();
                params = $.extend(this.model.toJSON(), {
                    permalink: this.model.urlFor('retrieve')
                });
                if (!this.model.get('anonymous')) {
                    params = $.extend(params, {
                        user: {
                            username: this.model.username,
                            user_url: this.model.user_url
                        }
                    });
                }
                this.$el.html(_.template($("#profile-thread-template").html())(params));
                this.$("span.timeago").timeago();
                element = this.$(".post-body");
                if (typeof MathJax !== "undefined" && MathJax !== null) {
                    MathJax.Hub.Queue(["Typeset", MathJax.Hub, element[0]]);
                }
                return this;
            };

            DiscussionThreadProfileView.prototype.convertMath = function() {
                return this.model.set(
                    'markdownBody',
                    DiscussionUtil.postMathJaxProcessor(DiscussionUtil.markdownWithHighlight(this.model.get('body')))
                );
            };

            DiscussionThreadProfileView.prototype.abbreviateBody = function() {
                var abbreviated;
                abbreviated = DiscussionUtil.abbreviateHTML(this.model.get('markdownBody'), 140);
                return this.model.set('abbreviatedBody', abbreviated);
            };

            return DiscussionThreadProfileView;

        })(Backbone.View);
    }

}).call(window);
