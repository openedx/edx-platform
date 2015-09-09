;(function (define) {
    'use strict';
    define(['teams/js/collections/base', 'teams/js/models/team', 'gettext'],
        function(BaseCollection, TeamModel, gettext) {
            var TeamCollection = BaseCollection.extend({
                sortField: 'last_activity_at',

                initialize: function(teams, options) {
                    var self = this;
                    BaseCollection.prototype.initialize.call(this, options);

                    this.server_api = _.extend(
                        {
                            topic_id: this.topic_id = options.topic_id,
                            expand: 'user',
                            course_id: function () { return encodeURIComponent(self.course_id); },
                            order_by: function () { return self.searchString ? '' : this.sortField; }
                        },
                        BaseCollection.prototype.server_api
                    );
                    delete this.server_api.sort_order; // Sort order is not specified for the Team API

                    this.registerSortableField('last_activity_at', gettext('last activity'));
                    this.registerSortableField('open_slots', gettext('open slots'));
                },

                model: TeamModel
            });
            return TeamCollection;
        });
}).call(this, define || RequireJS.define);
