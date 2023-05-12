// eslint-disable-next-line no-undef
define(['jquery', 'js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils'],
    function($, BaseView, HtmlUtils) {
        return BaseView.extend({
            className: function() {
                return 'new-component-templates new-component-' + this.model.type;
            },
            initialize: function() {
                BaseView.prototype.initialize.call(this);
                /* eslint-disable-next-line camelcase, no-var */
                var template_name = this.model.type === 'problem' ? 'add-xblock-component-menu-problem'
                    : 'add-xblock-component-menu';
                /* eslint-disable-next-line camelcase, no-var */
                var support_indicator_template = this.loadTemplate('add-xblock-component-support-level');
                /* eslint-disable-next-line camelcase, no-var */
                var support_legend_template = this.loadTemplate('add-xblock-component-support-legend');
                this.template = this.loadTemplate(template_name);
                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.HTML(this.template({
                        type: this.model.type,
                        templates: this.model.templates,
                        support_legend: this.model.support_legend,
                        // eslint-disable-next-line camelcase
                        support_indicator_template: support_indicator_template,
                        // eslint-disable-next-line camelcase
                        support_legend_template: support_legend_template,
                        HtmlUtils: HtmlUtils
                    }))
                );
                // Make the tabs on problems into "real tabs"
                this.$('.tab-group').tabs();
            }
        });
    }); // end define();
