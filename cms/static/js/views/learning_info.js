// Backbone Application View: Course Learning Information

// eslint-disable-next-line no-undef
define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/utils/templates',
    'edx-ui-toolkit/js/utils/html-utils'
],
function($, _, Backbone, gettext, TemplateUtils, HtmlUtils) {
    'use strict';

    // eslint-disable-next-line no-var
    var LearningInfoView = Backbone.View.extend({

        events: {
            'click .delete-course-learning-info': 'removeLearningInfo'
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
            $('li.course-settings-learning-fields').empty();
            // eslint-disable-next-line no-var
            var self = this;
            /* eslint-disable-next-line camelcase, no-var */
            var learning_information = this.model.get('learning_info');
            $.each(learning_information, function(index, info) {
                // eslint-disable-next-line no-var
                var attributes = {
                    index: index,
                    info: info,
                    // eslint-disable-next-line camelcase
                    info_count: learning_information.length
                };
                $(self.el).append(HtmlUtils.HTML(self.template(attributes)).toString());
            });
        },

        removeLearningInfo: function(event) {
            /*
            * Remove course learning fields.
            * */
            event.preventDefault();
            // eslint-disable-next-line no-var
            var index = event.currentTarget.getAttribute('data-index'),
                // eslint-disable-next-line camelcase
                existing_info = _.clone(this.model.get('learning_info'));
            // eslint-disable-next-line camelcase
            existing_info.splice(index, 1);
            this.model.set('learning_info', existing_info);
        }

    });
    return LearningInfoView;
});
