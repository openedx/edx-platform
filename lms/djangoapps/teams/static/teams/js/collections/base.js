;(function (define) {
    'use strict';
    define(['common/js/components/collections/paging_collection'],
        function(PagingCollection) {
            var BaseCollection = PagingCollection.extend({
                initialize: function(options) {
                    PagingCollection.prototype.initialize.call(this);

                    this.course_id = options.course_id;
                    this.perPage = options.per_page;

                    this.teamEvents = options.teamEvents;
                    this.teamEvents.bind('teams:update', this.onUpdate, this);
                },

                onUpdate: function(event) {
                    // Mark the collection as stale so that it knows to refresh when needed.
                    this.isStale = true;
                }
            });
            return BaseCollection;
        });
}).call(this, define || RequireJS.define);
