;(function (define) {
    'use strict';
    define([
      "js/ccx/view/ccx_schedule",
      "js/ccx/collection/schedule_collection"
    ], function(CcxScheduleView, ScheduleCollection) {
        return function ($container, scheduleJson, saveUrl) {
            var scheduleCollection = new ScheduleCollection(scheduleJson);
            var view = new CcxScheduleView({
                el: $container,
                saveCCXScheduleUrl: saveUrl,
                collection: scheduleCollection
            });
            return view;
        };
    });
}).call(this, define || RequireJS.define);
