/**
 * Model for Course Programs.
 */
(function (define) {
    'use strict';
    define([
            'backbone'
        ], 
        function (Backbone) {
        return Backbone.Model.extend({
            initialize: function(data) {
                if (data){
                    this.context = data;
                    //we should populate our model by looking at the run_modes
                    if (data.run_modes.length > 0){
                        //We only have 1 run mode for this program
                        this.setActiveRunMode(data.run_modes[0]);
                    }
                }
            },

            setActiveRunMode: function(runMode){
                this.set({
                    display_name: this.context.display_name,
                    key: this.context.key,
                    marketing_url: runMode.marketing_url || '',
                    start_date: runMode.start_date,
                    end_date: runMode.end_date,
                    is_enrolled: runMode.is_enrolled,
                    course_url: runMode.course_url || '',
                    course_image_url: runMode.course_image_url || '',
                    mode_slug: runMode.mode_slug
                });
            }
        });
    });
}).call(this, define || RequireJS.define);
