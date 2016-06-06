(function(define) {
    'use strict';

    define([
        'underscore',
        'jquery',
        'backbone',
        'gettext',
        'URI',
        'edx-ui-toolkit/js/utils/html-utils',
        'common/js/components/utils/view_utils',
        'common/js/discussion/discussion',
        'common/js/discussion/utils',
        'common/js/discussion/views/discussion_thread_profile_view',
        'text!discussion/templates/user-profile.underscore',
        'text!common/templates/discussion/pagination.underscore'
    ],
        function(_, $, Backbone, gettext, URI, HtmlUtils, ViewUtils, Discussion, DiscussionUtil,
                 DiscussionThreadProfileView, userProfileTemplate, paginationTemplate) {
            var DiscussionUserProfileView = Backbone.View.extend({
                events: {
                    'click .discussion-paginator a': 'changePage'
                },

                initialize: function(options) {
                    Backbone.View.prototype.initialize.call(this);
                    this.page = options.page;
                    this.numPages = options.numPages;
                    this.discussion = new Discussion();
                    this.discussion.on('reset', _.bind(this.render, this));
                    this.discussion.reset(this.collection, {silent: false});
                },

                render: function() {
                    var self = this,
                        baseUri = URI(window.location).removeSearch('page'),
                        pageUrlFunc,
                        paginationParams;
                    HtmlUtils.setHtml(this.$el, HtmlUtils.template(userProfileTemplate)({
                        threads: self.discussion.models
                    }));
                    this.discussion.map(function(thread) {
                        var view = new DiscussionThreadProfileView({
                            el: self.$('article#thread_' + thread.id),
                            model: thread
                        });
                        view.render();
                        return view;
                    });
                    pageUrlFunc = function(page) {
                        baseUri.clone().addSearch('page', page);
                    };
                    paginationParams = DiscussionUtil.getPaginationParams(this.page, this.numPages, pageUrlFunc);
                    HtmlUtils.setHtml(
                        this.$el.find('.discussion-pagination'),
                        HtmlUtils.template(paginationTemplate)(paginationParams)
                    );
                    return this;
                },

                changePage: function(event) {
                    var self = this,
                        url;
                    event.preventDefault();
                    url = $(event.target).attr('href');
                    DiscussionUtil.safeAjax({
                        $elem: this.$el,
                        $loading: $(event.target),
                        takeFocus: true,
                        url: url,
                        type: 'GET',
                        dataType: 'json',
                        success: function(response) {
                            self.page = response.page;
                            self.numPages = response.num_pages;
                            self.discussion.reset(response.discussion_data, {silent: false});
                            history.pushState({}, '', url);
                            ViewUtils.setScrollTop(0);
                        },
                        error: function() {
                            DiscussionUtil.discussionAlert(
                                gettext('Sorry'),
                                gettext('We had some trouble loading the page you requested. Please try again.')
                            );
                        }
                    });
                }
            });

            return DiscussionUserProfileView;
        });
}).call(this, define || RequireJS.define);
