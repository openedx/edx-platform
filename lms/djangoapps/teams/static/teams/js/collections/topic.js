;(function (define) {
    'use strict';
    define(['common/js/components/collections/paging_collection', 'teams/js/models/topic', 'gettext'],
        function(PagingCollection, TopicModel, gettext) {
            var TopicCollection = PagingCollection.extend({
                initialize: function(topics, options) {
                    PagingCollection.prototype.initialize.call(this);

                    this.course_id = options.course_id;
                    this.perPage = topics.results.length;
                    this.server_api['course_id'] = function () { return encodeURIComponent(this.course_id); };
                    this.server_api['order_by'] = function () { return this.sortField; };
                    delete this.server_api['sort_order']; // Sort order is not specified for the Team API

                    this.registerSortableField('name', gettext('name'));
                    this.registerSortableField('team_count', gettext('team count'));
                },

                model: TopicModel
            });
            return TopicCollection;
    });
}).call(this, define || RequireJS.define);
