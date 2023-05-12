// eslint-disable-next-line no-unused-vars
/* globals DiscussionContentShowView, DiscussionUtil, MathJax */
(function() {
    'use strict';

    // eslint-disable-next-line no-var
    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            /* eslint-disable-next-line no-var, no-restricted-syntax */
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

    // eslint-disable-next-line no-undef
    if (typeof Backbone !== 'undefined' && Backbone !== null) {
        this.ThreadResponseShowView = (function(_super) {
            // eslint-disable-next-line no-use-before-define
            __extends(ThreadResponseShowView, _super);

            function ThreadResponseShowView() {
                return ThreadResponseShowView.__super__.constructor.apply(this, arguments);
            }

            ThreadResponseShowView.prototype.initialize = function() {
                ThreadResponseShowView.__super__.initialize.call(this);
                return this.listenTo(this.model, 'change', this.render);
            };

            ThreadResponseShowView.prototype.renderTemplate = function() {
                // eslint-disable-next-line no-var
                var template = edx.HtmlUtils.template($('#thread-response-show-template').html()),
                    // eslint-disable-next-line no-undef
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
                this.$el.find('.posted-details .timeago').timeago();
                this.convertMath();
                return this;
            };

            ThreadResponseShowView.prototype.convertMath = function() {
                DiscussionUtil.convertMath(this.$('.response-body'));
            };

            ThreadResponseShowView.prototype.edit = function(event) {
                return this.trigger('response:edit', event);
            };

            ThreadResponseShowView.prototype._delete = function(event) {
                return this.trigger('response:_delete', event);
            };

            return ThreadResponseShowView;
        }(DiscussionContentShowView));
    }
}).call(window);
