define(["jquery", "js/views/baseview", 'edx-ui-toolkit/js/utils/html-utils'],
    function ($, BaseView, HtmlUtils) {

        return BaseView.extend({
            className: function () {
                return "new-component-templates new-component-" + this.model.type;
            },
            initialize: function () {
                BaseView.prototype.initialize.call(this);
                var template_name = this.model.type === "problem" ? "add-xblock-component-menu-problem" :
                    "add-xblock-component-menu";
                var support_indicator_template = this.loadTemplate("add-xblock-component-support-level");
                var support_legend_template = this.loadTemplate("add-xblock-component-support-legend");
                this.template = this.loadTemplate(template_name);
                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.HTML(this.template({
                        type: this.model.type, templates: this.model.templates,
                        support_legend: this.model.support_legend,
                        support_indicator_template: support_indicator_template,
                        support_legend_template: support_legend_template,
                        HtmlUtils: HtmlUtils
                    }))
                );
                // Make the tabs on problems into "real tabs"
                this.$('.tab-group').tabs();
            }
        });

    }); // end define();