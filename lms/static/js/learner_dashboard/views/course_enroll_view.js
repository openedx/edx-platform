;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!../../../templates/learner_dashboard/course_enroll.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             pageTpl
         ) {
            return Backbone.View.extend({
                tpl: HtmlUtils.template(pageTpl),

                events: {
                    'click .enroll-button': 'handleEnroll',
                    'change .run-select': 'handleRunSelect',
                },

                initialize: function(options) {
                    this.$parentEl = options.$parentEl;
                    this.enrollModel = options.enrollModel;
                    this.urlModel = options.urlModel;
                    this.render();
                    if (this.urlModel){
                        this.trackSelectionUrl = this.urlModel.get('track_selection_url');
                    }
                },

                render: function() {
                    var filledTemplate;
                    if (this.$parentEl && this.enrollModel){
                        filledTemplate = this.tpl(this.model.toJSON());
                        HtmlUtils.setHtml(this.$el, filledTemplate);
                        HtmlUtils.setHtml(this.$parentEl, HtmlUtils.HTML(this.$el));
                    }
                },

                handleEnroll: function(){
                    //Enrollment click event handled here
                    if (!this.model.get('course_key')){
                        this.$('.select-error').css('visibility','visible');
                    } else if (!this.model.get('is_enrolled')){
                        // actually enroll
                        this.enrollModel.save({
                            course_id: this.model.get('course_key')
                        }, {
                            success: _.bind(this.enrollSuccess, this),
                            error: _.bind(this.enrollError, this)
                        });
                    }
                },

                handleRunSelect: function(event){
                    var runKey;
                    if (event.target){
                        runKey = $(event.target).val();
                        if (runKey){
                            this.model.updateRun(runKey);
                        } else {
                            //Set back the unselected states
                            this.model.setUnselected();
                        }
                    }
                },

                enrollSuccess: function(){
                    var courseKey = this.model.get('course_key');
                    if (this.trackSelectionUrl) {
                        // Go to track selection page
                        this.redirect( this.trackSelectionUrl + courseKey );
                    } else {
                        this.model.set({
                            is_enrolled: true
                        });
                    }
                },

                enrollError: function(model, response) {

                    if (response.status === 403 && response.responseJSON.user_message_url) {
                        /**
                         * Check if we've been blocked from the course
                         * because of country access rules.
                         * If so, redirect to a page explaining to the user
                         * why they were blocked.
                         */
                        this.redirect( response.responseJSON.user_message_url );
                    } else if (this.trackSelectionUrl){
                        /**
                         * Otherwise, go to the track selection page as usual.
                         * This can occur, for example, when a course does not
                         * have a free enrollment mode, so we can't auto-enroll.
                         */
                        this.redirect( this.trackSelectionUrl + this.model.get('course_key') );
                    }
                },

                redirect: function( url ) {
                    window.location.href = url;
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
