var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicItemView = Backbone.View.extend({
        events : {
            'change .discussion-topic': 'toggleTopicCheck',
            'click .cohort-coursewide-discussions-form .action-save': 'saveCoursewideDiscussionsForm'
        },

        initialize: function(options) {
            this.template = _.template($('#cohort-discussion-topics-tpl').text());
            this.context = options.context;
            this.model.get('entries').on("change", this.toggleSaveButton, this);
            _.bindAll(this, 'toggleTopicCheck');
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
            return this;
        }

    });
}).call(this, $, _, Backbone, gettext, interpolate_text);
