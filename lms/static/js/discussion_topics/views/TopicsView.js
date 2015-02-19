var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text) {
    'use strict';

    var hiddenClass = 'is-hidden',
        disabledClass = 'is-disabled';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsView = Backbone.View.extend({
        events : {
            'check .discussion-topic': 'toggleTopicCheck'
        },

        initialize: function(options) {
            //var model = this.model;

            this.template = _.template($('#cohort-discussion-topics-tpl').text());
            this.context = options.context;

            //model.on('sync', this.onSync, this);
            //
            //// Update cohort counts when the user clicks back on the cohort management tab
            //// (for example, after uploading a csv file of cohort assignments and then
            //// checking results on data download tab).
            //$(this.getSectionCss('cohort_management')).click(function () {
            //    model.fetch();
            //});
        },

        render: function() {
            this.$el.html(this.template({
                coursewideTopics: this.model.get('entries')
            }));
            return this;
        },
        toggleTopicCheck: function (event) {
            event.preventDefault();
        },
        getCohortState: function() {
            return this.$('.discussion-topic').prop('checked');
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text);
