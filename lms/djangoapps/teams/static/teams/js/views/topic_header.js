;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'text!teams/templates/topic-header.underscore'
    ], function (Backbone, _, gettext, headerTemplate) {
        var TopicHeader = Backbone.View.extend({
            initialize: function (options) {
                this.collections = options.collection;
                this.collection.bind('add', _.bind(this.render, this));
                this.collection.bind('remove', _.bind(this.render, this));
                this.collection.bind('reset', _.bind(this.render, this));
            },

            render: function () {
                var message,
                    start = this.collection.start,
                    end = start + this.collection.length,
                    num_topics = this.collection.totalCount;
                if (!this.collection.hasPreviousPage() && !this.collection.hasNextPage()) {
                    // Only one page of results
                    message = interpolate(
                        ngettext(
                            // Translators: 'num_topics' is the number of topics that the student sees
                            'Currently viewing %(num_topics)s topic',
                            'Currently viewing all %(num_topics)s topics',
                            num_topics
                        ),
                        {num_topics: num_topics}, true
                    );
                } else {
                    // Many pages of results
                    message = interpolate(
                        gettext('Currently viewing %(first_index)s through %(last_index)s of %(num_topics)s topics'),
                        {first_index: Math.min(start + 1, end), last_index: end, num_topics: num_topics}, true
                    );
                }
                this.$el.html(_.template(headerTemplate, {message: message}));
                return this;
            }
        });
        return TopicHeader;
    });
}).call(this, define || RequireJS.define);
