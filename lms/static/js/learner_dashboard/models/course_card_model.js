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
                    this.setActiveRunMode(this.getRunMode(data.run_modes));
                }
            },

            getRunMode: function(runModes){
                //we should populate our model by looking at the run_modes
                if (runModes.length > 0){
                    if(runModes.length === 1){
                        return runModes[0];
                    }else{
                        //We need to implement logic here to select the
                        //most relevant run mode for the student to enroll
                        return runModes[0];
                    }
                }else{
                    return null;
                } 
            },

            setActiveRunMode: function(runMode){
                if (runMode){
                    this.set({
                        certificate_url: runMode.certificate_url,
                        course_image_url: runMode.course_image_url || '',
                        course_key: runMode.course_key,
                        course_url: runMode.course_url || '',
                        display_name: this.context.display_name,
                        end_date: runMode.end_date,
                        is_enrolled: runMode.is_enrolled,
                        is_enrollment_open: runMode.is_enrollment_open,
                        key: this.context.key,
                        marketing_url: runMode.marketing_url || '',
                        mode_slug: runMode.mode_slug,
                        run_key: runMode.run_key,
                        start_date: runMode.start_date
                    });
                }
            },

            updateRun: function(runKey){
                var selectedRun = _.findWhere(this.get('run_modes'), {run_key: runKey});
                if (selectedRun){
                    this.setActiveRunMode(selectedRun);
                }
            }
        });
    });
}).call(this, define || RequireJS.define);
