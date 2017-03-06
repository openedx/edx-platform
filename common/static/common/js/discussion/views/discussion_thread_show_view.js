/* globals DiscussionUtil, DiscussionContentShowView, MathJax */
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
        this.DiscussionThreadShowView = (function(_super) {
            __extends(DiscussionThreadShowView, _super);

            function DiscussionThreadShowView() {
                return DiscussionThreadShowView.__super__.constructor.apply(this, arguments);
            }

            DiscussionThreadShowView.prototype.initialize = function(options) {
                var _ref;
                DiscussionThreadShowView.__super__.initialize.call(this);
                this.mode = options.mode || 'inline';
                if ((_ref = this.mode) !== 'tab' && _ref !== 'inline') {
                    throw new Error('invalid mode: ' + this.mode);
                }
            };

            DiscussionThreadShowView.prototype.renderTemplate = function() {
                var context;
                context = $.extend({
                    mode: this.mode,
                    flagged: this.model.isFlagged(),
                    author_display: this.getAuthorDisplay(),
                    cid: this.model.cid,
                    readOnly: $('.discussion-module').data('read-only')
                }, this.model.attributes);
                return edx.HtmlUtils.template($('#thread-show-template').html())(context);
            };

            DiscussionThreadShowView.prototype.render = function() {
                edx.HtmlUtils.setHtml(
                    this.$el,
                    this.renderTemplate()
                );
                this.delegateEvents();
                this.renderAttrs();
                this.$('span.timeago').timeago();
                this.convertMath();
                this.$('.post-body');
                this.$('h1,h3');
                return this;
            };

            DiscussionThreadShowView.prototype.convertMath = function() {
                DiscussionUtil.convertMath(this.$('.post-body'));
            };

            DiscussionThreadShowView.prototype.edit = function(event) {
                return this.trigger('thread:edit', event);
            };

            DiscussionThreadShowView.prototype._delete = function(event) {
                return this.trigger('thread:_delete', event);
            };

            DiscussionThreadShowView.prototype.highlight = function(el) {
                if (el.html()) {
                    return el.html(el.html().replace(/&lt;mark&gt;/g, "<mark>").replace(/&lt;\/mark&gt;/g, "</mark>"));
                }
            };

            return DiscussionThreadShowView;
        })(DiscussionContentShowView);
    }
}).call(window);
