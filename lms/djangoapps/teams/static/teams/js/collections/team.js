;(function (define) {
    'use strict';
    define(['common/js/components/collections/paging_collection', 'teams/js/models/team', 'gettext'],
        function(PagingCollection, TeamModel, gettext) {
            var TeamCollection = PagingCollection.extend({
                initialize: function(teams, options) {
                    PagingCollection.prototype.initialize.call(this);

                    this.course_id = options.course_id;
                    this.server_api['topic_id'] = this.topic_id = options.topic_id;
                    this.perPage = options.per_page;
                    this.server_api['course_id'] = function () { return encodeURIComponent(this.course_id); };
                    this.server_api['order_by'] = function () { return 'name'; }; // TODO surface sort order in UI
                    delete this.server_api['sort_order']; // Sort order is not specified for the Team API

                    this.registerSortableField('name', gettext('name'));
                    this.registerSortableField('open_slots', gettext('open_slots'));
                },

                model: TeamModel
            });
            return TeamCollection;
    });
}).call(this, define || RequireJS.define);
