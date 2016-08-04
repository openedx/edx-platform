// Backbone Application View: Course Learning Information

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/utils/templates'
],
function ($, _, Backbone, gettext, TemplateUtils) {
    'use strict';
    var LearningInfoView = Backbone.View.extend({

        events: {
            'click .delete-course-learning-info': "removeLearningInfo"
        },

        initialize: function() {
            // Set up the initial state of the attributes set for this model instance
             _.bindAll(this, 'render');
            this.template = this.loadTemplate('course-settings-learning-fields');
            this.listenTo(this.model, 'change:learning_info', this.render);
        },

        loadTemplate: function(name) {
            // Retrieve the corresponding template for this model
            return TemplateUtils.loadTemplate(name);
        },

        render: function() {
             // rendering for this model
            $("li.course-settings-learning-fields").empty();
            var self = this;
            var learning_information = this.model.get('learning_info');
            $.each(learning_information, function( index, info ) {
                $(self.el).append(self.template({index: index, info: info, info_count: learning_information.length }));
            });
        },

        removeLearningInfo: function(event) {
            /*
            * Remove course learning fields.
            * */
            event.preventDefault();
            var index = event.currentTarget.getAttribute('data-index'),
                existing_info = _.clone(this.model.get('learning_info'));
            existing_info.splice(index, 1);
            this.model.set('learning_info', existing_info);
        }

    });
    return LearningInfoView;
});
