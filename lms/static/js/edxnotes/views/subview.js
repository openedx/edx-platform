;(function (define, undefined) {
'use strict';
define(['underscore', 'backbone'],
function (_, Backbone) {
    var SubView = Backbone.View.extend({
        className: 'edx-notes-page-items-list',
        templateName: '',
        initialize: function (options) {
            this.options = options;
            if (this.templateName) {
                this.template = this.loadTemplate(this.templateName);
            }
        },

        render: function () {
            return this;
        },

        loadTemplate: function (name) {
            var templateSelector = "#" + name + "-tpl",
                templateText = $(templateSelector).text();

            if (!templateText) {
                console.error("Failed to load " + name + " template");
            }

            return _.template(templateText);
        }
    });

    return SubView;
});
}).call(this, define || RequireJS.define);
