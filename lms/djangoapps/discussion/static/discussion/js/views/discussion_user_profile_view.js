/* globals Discussion, DiscussionThreadProfileView, DiscussionUtil, URI */
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
        this.DiscussionUserProfileView = (function(_super) {
            __extends(DiscussionUserProfileView, _super);

            function DiscussionUserProfileView() {
                var self = this;
                this.render = function() {
                    return DiscussionUserProfileView.prototype.render.apply(self, arguments);
                };
                return DiscussionUserProfileView.__super__.constructor.apply(this, arguments);
            }

            DiscussionUserProfileView.prototype.events = {
                'click .discussion-paginator a': 'changePage'
            };

            DiscussionUserProfileView.prototype.initialize = function(options) {
                DiscussionUserProfileView.__super__.initialize.call(this);
                this.page = options.page;
                this.numPages = options.numPages;
                this.discussion = new Discussion();
                this.discussion.on('reset', this.render);
                return this.discussion.reset(this.collection, {
                    silent: false
                });
            };

            DiscussionUserProfileView.prototype.render = function() {
                var baseUri, pageUrlFunc, paginationParams,
                    self = this;
                this.$el.html(_.template($('#user-profile-template').html())({
                    threads: this.discussion.models
                }));
                this.discussion.map(function(thread) {
                    return new DiscussionThreadProfileView({
                        el: self.$('article#thread_' + thread.id),
                        model: thread
                    }).render();
                });
                baseUri = URI(window.location).removeSearch('page');
                pageUrlFunc = function(page) {
                    return baseUri.clone().addSearch('page', page);
                };
                paginationParams = DiscussionUtil.getPaginationParams(this.page, this.numPages, pageUrlFunc);
                this.$el.find('.discussion-pagination')
                    .html(_.template($('#pagination-template').html())(paginationParams));
            };

            DiscussionUserProfileView.prototype.changePage = function(event) {
                var url,
                    self = this;
                event.preventDefault();
                url = $(event.target).attr('href');
                return DiscussionUtil.safeAjax({
                    $elem: this.$el,
                    $loading: $(event.target),
                    takeFocus: true,
                    url: url,
                    type: 'GET',
                    dataType: 'json',
                    success: function(response) {
                        self.page = response.page;
                        self.numPages = response.num_pages;
                        self.discussion.reset(response.discussion_data, {
                            silent: false
                        });
                        history.pushState({}, '', url);
                        return $('html, body').animate({
                            scrollTop: 0
                        });
                    },
                    error: function() {
                        return DiscussionUtil.discussionAlert(
                            gettext('Sorry'),
                            gettext('We had some trouble loading the page you requested. Please try again.')
                        );
                    }
                });
            };

            return DiscussionUserProfileView;
        })(Backbone.View);
    }
}).call(window);
