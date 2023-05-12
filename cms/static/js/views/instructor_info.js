// Backbone Application View: Instructor Information

// eslint-disable-next-line no-undef
define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/utils/templates',
    'js/models/uploads',
    'js/views/uploads',
    'edx-ui-toolkit/js/utils/html-utils'
],
function($, _, Backbone, gettext, TemplateUtils, FileUploadModel, FileUploadDialog, HtmlUtils) {
    'use strict';

    // eslint-disable-next-line no-var
    var InstructorInfoView = Backbone.View.extend({

        events: {
            'click .remove-instructor-data': 'removeInstructor',
            'click .action-upload-instructor-image': 'uploadInstructorImage'
        },

        initialize: function() {
            // Set up the initial state of the attributes set for this model instance
            _.bindAll(this, 'render');
            this.template = this.loadTemplate('course-instructor-details');
            this.listenTo(this.model, 'change:instructor_info', this.render);
        },

        loadTemplate: function(name) {
            // Retrieve the corresponding template for this model
            return TemplateUtils.loadTemplate(name);
        },

        render: function() {
            // eslint-disable-next-line no-var
            var attributes;
            // Assemble the render view for this model.
            $('.course-instructor-details-fields').empty();
            // eslint-disable-next-line no-var
            var self = this;
            $.each(this.model.get('instructor_info').instructors, function(index, data) {
                attributes = {
                    data: data,
                    index: index
                };
                $(self.el).append(HtmlUtils.HTML(self.template(attributes)).toString());
            });

            // Avoid showing broken image on mistyped/nonexistent image
            this.$el.find('img').error(function() {
                $(this).hide();
            });
            this.$el.find('img').load(function() {
                $(this).show();
            });
        },

        removeInstructor: function(event) {
            /*
                 * Remove course Instructor fields.
                 * */
            event.preventDefault();
            // eslint-disable-next-line no-var
            var index = event.currentTarget.getAttribute('data-index'),
                instructors = this.model.get('instructor_info').instructors.slice(0);
            instructors.splice(index, 1);
            this.model.set('instructor_info', {instructors: instructors});
        },

        uploadInstructorImage: function(event) {
            /*
                * Upload instructor image.
                * */
            event.preventDefault();
            // eslint-disable-next-line no-var
            var index = event.currentTarget.getAttribute('data-index'),
                instructors = this.model.get('instructor_info').instructors.slice(0),
                instructor = instructors[index];

            // eslint-disable-next-line no-var
            var upload = new FileUploadModel({
                title: gettext('Upload instructor image.'),
                message: gettext('Files must be in JPEG or PNG format.'),
                mimeTypes: ['image/jpeg', 'image/png']
            });
            // eslint-disable-next-line no-var
            var self = this;
            // eslint-disable-next-line no-var
            var modal = new FileUploadDialog({
                model: upload,
                onSuccess: function(response) {
                    instructor.image = response.asset.url;
                    self.model.set('instructor_info', {instructors: instructors});
                    self.model.trigger('change', self.model);
                    self.model.trigger('change:instructor_info', self.model);
                }
            });
            modal.show();
        }
    });
    return InstructorInfoView;
});
