;(function (define) {
    'use strict';
    define(['underscore', 'gettext', 'teams/js/collections/base', 'teams/js/models/topic'],
        function(_, gettext, BaseCollection, TopicModel) {
            var TopicCollection = BaseCollection.extend({
                initialize: function(topics, options) {
                    var self = this;

                    BaseCollection.prototype.initialize.call(this, options);

                    this.perPage = topics.results.length;

                    this.server_api = _.extend(
                        {
                            course_id: function () { return encodeURIComponent(self.course_id); },
                            order_by: function () { return this.sortField; }
                        },
                        BaseCollection.prototype.server_api
                    );
                    delete this.server_api['sort_order']; // Sort order is not specified for the Team API

                    this.registerSortableField('name', gettext('name'));
                    // Translators: This refers to the number of teams (a count of how many teams there are)
                    this.registerSortableField('team_count', gettext('team count'));
                },

                onUpdate: function(event) {
                    if (_.contains(['create', 'delete'], event.action)) {
                        this.isStale = true;
                    }
                },

                model: TopicModel
            });
            return TopicCollection;
        });
}).call(this, define || RequireJS.define);
