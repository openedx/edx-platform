define([
        'backbone',
        'jquery',
        'underscore',
        'text!templates/programs/course_run.underscore',
        'edx-ui-toolkit/js/utils/html-utils'
    ],
    function ( Backbone, $, _, CourseRunTpl, HtmlUtils ) {
        'use strict';

        return Backbone.View.extend({
            events: {
                'change .js-course-run-select': 'selectRun',
                'click .js-remove-run': 'removeRun'
            },

            tpl: HtmlUtils.template( CourseRunTpl ),

            initialize: function( options ) {
                /**
                 * Need the run model for the template, and the courseModel
                 * to keep parent view up to date with run changes
                 */
                this.courseModel = options.courseModel;
                this.courseRuns = options.courseRuns;
                this.programStatus = options.programStatus;

                this.model.on('change', this.render, this);
                this.courseRuns.on('update', this.updateDropdown, this);

                this.$parentEl = options.$parentEl;
                this.render();
            },

            render: function() {
                var data = this.model.attributes;

                data.programStatus = this.programStatus;

                if ( !!this.courseRuns ) {
                    data.courseRuns = this.courseRuns.toJSON();
                }

                HtmlUtils.setHtml(this.$el, this.tpl( data ) );
                this.$parentEl.append( this.$el );
            },

            // Delete this view
            destroy: function() {
                this.undelegateEvents();
                this.remove();
            },

            // Data returned from courseList API is not the correct format
            formatData: function( data ) {
                return {
                    course_key: data.id,
                    mode_slug: 'verified',
                    start_date: data.start,
                    sku: ''
                };
            },

            removeRun: function() {
                // Update run_modes array on programModel
                var startDate = this.model.get('start_date'),
                    courseKey = this.model.get('course_key'),
                    /**
                     *  NB: cloning the array so the model will fire a change event when
                     *  the updated version is saved back to the model
                     */
                    runs = _.clone(this.courseModel.get('run_modes')),
                    updatedRuns = [];

                updatedRuns = _.reject( runs, function( obj ) {
                    return obj.start_date === startDate &&
                           obj.course_key === courseKey;
                });

                this.courseModel.set({
                    run_modes: updatedRuns
                });

                this.courseRuns.addRun(courseKey);

                this.destroy();
            },

            selectRun: function(event) {
                var id = $(event.currentTarget).val(),
                    runObj = _.findWhere(this.courseRuns.allRuns, {id: id}),
                    /**
                     *  NB: cloning the array so the model will fire a change event when
                     *  the updated version is saved back to the model
                     */
                    runs = _.clone(this.courseModel.get('run_modes')),
                    data = this.formatData(runObj);

                this.model.set( data );
                runs.push(data);
                this.courseModel.set({run_modes: runs});
                this.courseRuns.removeRun(id);
            },

            // If a run has not been selected update the dropdown options
            updateDropdown: function() {
                if ( !this.model.get('course_key') ) {
                    this.render();
                }
            }
        });
    }
);
