define([
    "jquery",
    "js/views/baseview",
    "text!templates/add-xblock-component-menu.underscore",
    "text!templates/add-xblock-component-menu-problem.underscore",
    "edx-ui-toolkit/js/utils/html-utils",
    "edx-ui-toolkit/js/utils/string-utils"],
    function (
        $,
        BaseView,
        AddXBlockComponentMenuTemplate,
        AddXBlockComponentMenuProblemTemplate,
        HtmlUtils,
        StringUtils
    ) {

        return BaseView.extend({
            className: function () {
                return "new-component-templates new-component-" + this.model.type;
            },
            initialize: function () {
                BaseView.prototype.initialize.call(this);
                var templateString = AddXBlockComponentMenuTemplate
                if (this.model.type === "problem") {
                    templateString = AddXBlockComponentMenuProblemTemplate
                };
                this.template = HtmlUtils.template(templateString);

                HtmlUtils.setHtml(
                    this.$el,
                    this.template({
                        type: this.model.type,
                        templates: this.model.templates,
                        StringUtils: StringUtils
                    })
                );
                // Make the tabs on problems into "real tabs"
                this.$('.tab-group').tabs();
            }
        });

    }); // end define();