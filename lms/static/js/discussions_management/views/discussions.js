(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext',
        'js/discussions_management/views/divided_discussions_inline',
        'js/discussions_management/views/divided_discussions_course_wide',
        'edx-ui-toolkit/js/utils/html-utils'
    ],

        function($, _, Backbone, gettext, InlineDiscussionsView, CourseWideDiscussionsView, HtmlUtils) {
            var DiscussionsView = Backbone.View.extend({

                initialize: function(options) {
                    this.template = HtmlUtils.template($('#discussions-tpl').text());
                    this.context = options.context;
                    this.discussionSettings = options.discussionSettings;
                },

                render: function() {
                    HtmlUtils.setHtml(this.$el, this.template({}));
                    this.showDiscussionTopics();
                    return this;
                },

                getSectionCss: function(section) {
                    return ".instructor-nav .nav-item [data-section='" + section + "']";
                },

                showDiscussionTopics: function() {
                    var dividedDiscussionsElement = this.$('.discussions-nav');
                    if (!this.CourseWideDiscussionsView) {
                        this.CourseWideDiscussionsView = new CourseWideDiscussionsView({
                            el: dividedDiscussionsElement,
                            model: this.context.courseDiscussionTopicDetailsModel,
                            discussionSettings: this.discussionSettings
                        }).render();
                    }

                    if (!this.InlineDiscussionsView) {
                        this.InlineDiscussionsView = new InlineDiscussionsView({
                            el: dividedDiscussionsElement,
                            model: this.context.courseDiscussionTopicDetailsModel,
                            discussionSettings: this.discussionSettings
                        }).render();
                    }
                }
            });
            return DiscussionsView;
        });
}).call(this, define || RequireJS.define);
