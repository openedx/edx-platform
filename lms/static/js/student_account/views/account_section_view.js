(function(define, undefined) {
    'use strict';
    define([
        'gettext',
        'jquery',
        'underscore',
        'backbone',
        'text!student_account/account_settings_section.underscore'
    ], function(gettext, $, _, Backbone, sectionTemplate) {
        var AccountSectionView = Backbone.View.extend({

            initialize: function(options) {
                this.options = options;
                _.bindAll(this, 'render', 'renderFields');
            },

            render: function() {
                this.$el.html(_.template(sectionTemplate)({
                    sections: this.options.sections,
                    tabName: this.options.tabName,
                    tabLabel: this.options.tabLabel
                }));

                this.renderFields();
            },

            renderFields: function() {
                var view = this;

                _.each(view.$('.' + view.options.tabName + '-section-body'), function(sectionEl, index) {
                    _.each(view.options.sections[index].fields, function(field) {
                        $(sectionEl).append(field.view.render().el);
                    });
                });
                return this;
            }
        });

        return AccountSectionView;
    });
}).call(this, define || RequireJS.define);
