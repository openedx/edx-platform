;(function (define) {
    'use strict';
    define(['underscore', 'gettext', 'teams/js/collections/base', 'teams/js/models/topic'],
        function(_, gettext, BaseCollection, TopicModel) {
            var TopicCollection = BaseCollection.extend({
                model: TopicModel,

                state: {
                    perPage: null,
                    sortKey: 'name'
                },

                queryParams: {
                    course_id: function () { return this.course_id; },
                    text_search: function () { return this.searchString || ''; }
                },

                constructor: function(topics, options) {
                    BaseCollection.prototype.constructor.call(this, topics, options);

                    this.state.pageSize = topics.results.length;
                    if (topics.sort_order) {
                        this.state.sortKey = topics.sort_order;
                    }
                    this.registerSortableField('name', gettext('name'));
                    // Translators: This refers to the number of teams (a count of how many teams there are)
                    this.registerSortableField('team_count', gettext('team count'));
                },

                onUpdate: function(event) {
                    if (_.contains(['create', 'delete'], event.action)) {
                        this.isStale = true;
                    }
                }
            });
            return TopicCollection;
        });
}).call(this, define || RequireJS.define);
