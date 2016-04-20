// Backbone Application View: Instructor Information

define([  // jshint ignore:line
        'jquery',
        'underscore',
        'backbone',
        'gettext',
        'js/utils/templates',
        "js/models/uploads",
        "js/views/uploads"
    ],
    function ($, _, Backbone, gettext, TemplateUtils, FileUploadModel, FileUploadDialog) {
        'use strict';
        var InstructorInfoView = Backbone.View.extend({

             events : {
                 'click .remove-instructor-data': 'removeInstructor',
                 'click .action-upload-instructor-image': "uploadInstructorImage"
             },

            initialize: function(options) {
                // Set up the initial state of the attributes set for this model instance
                 _.bindAll(this, 'render');
                this.template = this.loadTemplate('course-instructor-details');
                this.model = options.model;
            },

            loadTemplate: function(name) {
                // Retrieve the corresponding template for this model
                return TemplateUtils.loadTemplate(name);
            },

            render: function() {
                // Assemble the render view for this model.
                $("span.course-instructor-details-fields").empty();
                var self = this;
                var instructors = this.model.get('instructor_info')['instructors'];
                $.each(instructors, function( index, data ) {
                    $(self.el).append(self.template({
                        data: data,
                        index: index,
                        instructors: instructors.length
                    }));
                });
            },

            removeInstructor: function(event) {
                /*
                 * Remove course Instructor fields.
                 * */
                event.preventDefault();
                var index = event.currentTarget.getAttribute('data-index'),
                    existing_info = _.clone(this.model.get('instructor_info'));
                existing_info['instructors'].splice(index, 1);
                this.model.set('instructor_info', existing_info);
                this.model.trigger("change:instructor_info", this.model );
                this.render();

            },

            uploadInstructorImage: function(event) {
                /*
                * Upload instructor image.
                * */
                event.preventDefault();
                var index = event.currentTarget.getAttribute('data-index'),
                    info = _.clone(this.model.get('instructor_info')),
                    instructor = info.instructors[index];

                var upload = new FileUploadModel({
                    title: gettext("Upload instructor image."),
                    message: gettext("Files must be in JPEG or PNG format."),
                    mimeTypes: ['image/jpeg', 'image/png']
                });
                var self = this;
                var modal = new FileUploadDialog({
                    model: upload,
                    onSuccess: function(response) {
                        var options = {
                            'instructor_image_asset_path': response.asset.url
                        };
                        instructor.image = options.instructor_image_asset_path;
                        self.model.set('instructor_info', info);
                        self.model.trigger("change:instructor_info");
                        self.render();
                    }
                });
                modal.show();
            }
        });
        return InstructorInfoView;
    });
