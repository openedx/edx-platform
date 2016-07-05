define([
        'backbone',
        'backbone.validation',
        'jquery',
        'underscore',
        'js/programs/collections/course_runs_collection',
        'js/programs/models/program_model',
        'js/programs/views/confirm_modal_view',
        'js/programs/views/course_details_view',
        'text!templates/programs/program_details.underscore',
        'edx-ui-toolkit/js/utils/html-utils',
        'gettext',
        'js/programs/utils/validation_config'
    ],
    function( Backbone, BackboneValidation, $, _, CourseRunsCollection,
        ProgramModel, ModalView, CourseView, ListTpl,
            HtmlUtils ) {
        'use strict';

        return Backbone.View.extend({
            el: '.js-program-admin',

            events: {
                'blur .js-inline-edit input': 'checkEdit',
                'click .js-add-course': 'addCourse',
                'click .js-enable-edit': 'editField',
                'click .js-publish-program': 'confirmPublish'
            },

            tpl: HtmlUtils.template( ListTpl ),

            initialize: function() {
                Backbone.Validation.bind( this );

                this.courseRuns = new CourseRunsCollection([], {
                    organization: this.model.get('organizations')[0]
                });
                this.courseRuns.fetch();
                this.courseRuns.on('sync', this.setAvailableCourseRuns, this);
                this.render();
            },

            render: function() {
                HtmlUtils.setHtml(this.$el, this.tpl( this.model.toJSON() ) );
                this.postRender();
            },

            postRender: function() {
                var courses = this.model.get( 'course_codes' );

                _.each( courses, function( course ) {
                    var title = course.key + 'Course';

                    this[ title ] = new CourseView({
                        courseRuns: this.courseRuns,
                        programModel: this.model,
                        courseData: course
                    });
                }.bind(this) );

                // Stop listening to the model sync set when publishing
                this.model.off( 'sync' );
            },

            addCourse: function() {
                return new CourseView({
                    courseRuns: this.courseRuns,
                    programModel: this.model
                });
            },

            checkEdit: function( event ) {
                var $input = $(event.target),
                    $span = $input.prevAll('.js-model-value'),
                    $btn = $input.next('.js-enable-edit'),
                    value = $input.val(),
                    key = $input.data('field'),
                    data = {};

                data[key] = value;

                $input.addClass('is-hidden');
                $btn.removeClass('is-hidden');
                $span.removeClass('is-hidden');

                if ( this.model.get( key ) !== value ) {
                    this.model.set( data );

                    if ( this.model.isValid( true ) ) {
                        this.model.patch( data );
                        $span.text( value );
                    }
                }
            },

            /**
             * Loads modal that user clicks a confirmation button
             * in to publish the course (or they can cancel out of it)
             */
            confirmPublish: function( event ) {
                event.preventDefault();

                /**
                 * Update validation to make marketing slug required
                 * Note that because this validation is not required for
                 * the program creation form and is only happening here
                 * it makes sense to have the validation at the view level
                 */
                if ( this.model.isValid( true ) && this.validateMarketingSlug() ) {
                    this.modalView = new ModalView({
                        model: this.model,
                        callback: _.bind( this.publishProgram, this ),
                        content: this.getModalContent(),
                        parentEl: '.js-publish-modal',
                        parentView: this
                    });
                }
            },

            editField: function( event ) {
                /**
                 * Making the assumption that users can only see
                 * programs that they have permission to edit
                 */
                var $btn = $( event.currentTarget ),
                    $el = $btn.prev( 'input' );

                event.preventDefault();

                $el.prevAll( '.js-model-value' ).addClass( 'is-hidden' );
                $el.removeClass( 'is-hidden' )
                   .addClass( 'edit' )
                   .focus();
                $btn.addClass( 'is-hidden' );
            },

            getModalContent: function() {
                /* jshint maxlen: 300 */
                return {
                    name: gettext('confirm'),
                    title: gettext('Publish this program?'),
                    body: gettext(
                        'After you publish this program, you cannot add or remove course codes or remove course runs.'
                    ),
                    cta: {
                        cancel: gettext('Cancel'),
                        confirm: gettext('Publish')
                    }
                };
            },

            publishProgram: function() {
                var data = {
                    status: 'active'
                };

                this.model.set( data, { silent: true } );
                this.model.on( 'sync', this.render, this );
                this.model.patch( data );
            },

            setAvailableCourseRuns: function() {
                var allRuns = this.courseRuns.toJSON(),
                    courses = this.model.get('course_codes'),
                    selectedRuns,
                    availableRuns = allRuns;

                if (courses.length) {
                    selectedRuns = _.pluck( courses, 'run_modes' );
                    selectedRuns = _.flatten( selectedRuns );
                }

                availableRuns = _.reject(allRuns, function(run) {
                    var selectedCourseRun = _.findWhere( selectedRuns, {
                        course_key: run.id,
                        start_date: run.start
                    });

                    return !_.isUndefined(selectedCourseRun);
                });

                this.courseRuns.set(availableRuns);
            },

            validateMarketingSlug: function() {
                var isValid = false,
                    $input = {},
                    $message = {};

                if ( this.model.get( 'marketing_slug' ).length > 0 ) {
                    isValid = true;
                } else {
                    $input = this.$el.find( '#program-marketing-slug' );
                    $message = $input.siblings( '.field-message' );

                    // Update DOM
                    $input.addClass( 'has-error' );
                    $message.addClass( 'has-error' );
                    $message.find( '.field-message-content' )
                        .text( gettext( 'Marketing Slug is required.') );
                }

                return isValid;
            }
        });
    }
);
