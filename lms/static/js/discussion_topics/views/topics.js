var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsView = Backbone.View.extend({
        events : {
            'change .discussion-topic': 'toggleTopicCheck'
        },

        initialize: function(options) {
            this.template = _.template($('#cohort-discussion-topics-tpl').text());
            this.context = options.context;
            _.bindAll(this, 'toggleTopicCheck');
        },

        render: function() {
            this.$el.html(this.template({
                coursewideTopics: this.model.get('entries'),
                inlineDiscussionTopics: this.model.get('subcategories')
            }));
            return this;
        },
        toggleTopicCheck: function (event) {
            event.preventDefault();

            var $selectedTopic = $(event.currentTarget),
                $cohortedText = $selectedTopic.siblings('span.cohorted-text'),
                isTopicChecked = $selectedTopic.prop('checked'),
                id = $selectedTopic.data('id');

            if(isTopicChecked) {
                this.element.show($cohortedText);
            }
            else {
                this.element.hide($cohortedText);
            }

            var currentModel = this.model.get('entries').get(id);
            currentModel.set({'is_cohorted': isTopicChecked});
            return;
        },
        element: {
            hide: function( $el ) {
                $el.addClass('hidden');
            },
            show: function( $el ) {
                $el.removeClass('hidden');
            }
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text);
