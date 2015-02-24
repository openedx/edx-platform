var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicItemView = Backbone.View.extend({
        events : {
        },

        initialize: function(options) {
            this.template = _.template($('#cohort-discussion-topics-tpl').text());
            this.context = options.context;
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
            return this;
        }

    });
}).call(this, $, _, Backbone, gettext, interpolate_text);
