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
                    this.isStale = false;
                },

                onUpdate: function(event) {
                    this.isStale = true;
                },

                /**
                 * Refreshes the collection if it has been marked as stale.
                 * @param force If true, it will always refresh.
                 * @returns {promise} Returns a promise representing the refresh
                 */
                refresh: function(force) {
                    var self = this,
                        deferred = $.Deferred();
                    if (force || this.isStale) {
                        this.setPage(1)
                            .done(function() {
                                self.isStale = false;
                                deferred.resolve();
                            });
                    } else {
                        deferred.resolve();
                    }
                    return deferred.promise();
                }
            });
            return BaseCollection;
        });
}).call(this, define || RequireJS.define);
