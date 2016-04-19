define([
    "js/views/baseview",
    "text!templates/add-xblock-component-button.underscore",
    "edx-ui-toolkit/js/utils/html-utils"
], function (BaseView, AddXBlockComponentButtonTemplate, HtmlUtils) {

        return BaseView.extend({
            tagName: "li",
            initialize: function () {
                BaseView.prototype.initialize.call(this);
                this.template = HtmlUtils.template(AddXBlockComponentButtonTemplate);
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        type: this.model.type,
                        templates: this.model.templates,
                        display_name: this.model.display_name
                    })
                );
            }
        });

    }); // end define();
